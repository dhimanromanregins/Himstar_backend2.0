# views.py
from rest_framework import generics
from .models import Like, Comment, Favorite, Share, Participant
from .serializers import LikeSerializer, CommentSerializer, FavoriteSerializer, ShareSerializer, ParticipantSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.files import File
# from utils.helpers import AzureMediaStorage, upload_video_to_azure

from django.conf import settings
import requests
from datetime import date
import os
from django.core.files.storage import default_storage
import uuid
import threading
from django.shortcuts import get_object_or_404
from accounts.models import Register
from rest_framework.permissions import IsAuthenticated
from dashboard.models import Competition
import subprocess
from django.utils.timezone import now
from django.core.files import File
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

today = now()


class ParticipantListCreateView(APIView):
    """
    Participant Management API
    
    Handles listing and creating participants for competitions.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get all participants",
        responses={
            200: openapi.Response(
                description="List of participants",
                schema=ParticipantSerializer(many=True)
            )
        },
        tags=['Participants']
    )
    def get(self, request):
        participants = Participant.objects.all()
        serializer = ParticipantSerializer(participants, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new participant for a competition",
        request_body=ParticipantSerializer,
        manual_parameters=[
            openapi.Parameter(
                'competition_pk',
                openapi.IN_PATH,
                description="Competition ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            201: openapi.Response(
                description="Participant created successfully",
                schema=ParticipantSerializer
            ),
            400: openapi.Response(description="Validation errors")
        },
        tags=['Participants']
    )
    def post(self, request, competition_pk):
        competition = Competition.objects.get(pk=competition_pk)
        serializer = ParticipantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(competition=competition)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ParticipantDetailView(APIView):
    """
    Participant Detail API
    
    Retrieves details of the current user's participation.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get current user's participant details",
        responses={
            200: openapi.Response(
                description="Participant details",
                schema=ParticipantSerializer
            ),
            404: openapi.Response(
                description="Participant not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Error message')
                    }
                )
            )
        },
        tags=['Participants']
    )
    def get(self, request):
        try:
            register = Register.objects.filter(user=request.user).first()
            participant = Participant.objects.get(user=register)
        except Participant.DoesNotExist:
            return Response({'detail': 'Participant not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ParticipantSerializer(participant)
        return Response(serializer.data)

    def put(self, request, pk):
        try:
            participant = Participant.objects.get(pk=pk)
        except Participant.DoesNotExist:
            return Response({'detail': 'Participant not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ParticipantSerializer(participant, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        competition_id = request.data['competition']
        register = Register.objects.filter(user=request.user).first()
        participant = Participant.objects.filter(competition=competition_id, user=register).first()
        if not participant:
            return Response({'detail': 'Participant not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Properly move the temp video to main video field
        if participant.temp_video:
            try:
                # Get the temp video file
                temp_file = participant.temp_video
                temp_path = temp_file.path if temp_file else None
                
                print(f"DEBUG PATCH: Moving temp video from: {temp_path}")
                print(f"DEBUG PATCH: Temp file exists: {os.path.exists(temp_path) if temp_path else False}")
                
                if temp_path and os.path.exists(temp_path):
                    # Read the temp file content
                    with open(temp_path, 'rb') as f:
                        django_file = File(f)
                        
                        # Generate new filename for main video
                        original_name = os.path.basename(temp_path)
                        new_name = f"main_{original_name}"
                        
                        # Save to main video field
                        participant.video.save(new_name, django_file, save=False)
                        print(f"DEBUG PATCH: Saved to main video: {participant.video}")
                    
                    # Clear temp video reference
                    participant.temp_video = None
                    
                    # Set payment status and save
                    participant.is_paid = True
                    participant.save()
                    
                    print(f"DEBUG PATCH: Participant saved, main video: {participant.video}")
                    
                    # DON'T clean up temp file immediately - let it stay for backup
                    # The file will be cleaned up later by scheduled cleanup or when user uploads new video
                    print(f"DEBUG PATCH: Keeping temp file for backup: {temp_path}")
                    
                    # Verify the main video file exists
                    if participant.video:
                        main_video_path = participant.video.path
                        print(f"DEBUG PATCH: Main video path: {main_video_path}")
                        print(f"DEBUG PATCH: Main video exists: {os.path.exists(main_video_path)}")
                    
                    # Only cleanup if we're absolutely sure the main video is saved correctly
                    # try:
                    #     if os.path.exists(temp_path) and participant.video and os.path.exists(participant.video.path):
                    #         os.remove(temp_path)
                    #         print(f"DEBUG PATCH: Cleaned up temp file: {temp_path}")
                    # except Exception as cleanup_err:
                    #     print(f"DEBUG PATCH: Error cleaning temp file: {cleanup_err}")
                    
                else:
                    return Response({
                        'detail': 'Temp video file not found on filesystem.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception as e:
                print(f"DEBUG PATCH: Error moving video: {e}")
                return Response({
                    'detail': f'Error processing video: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # No temp video, just update payment status
            participant.is_paid = True
            participant.save()
        
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            participant = Participant.objects.get(pk=pk)
        except Participant.DoesNotExist:
            return Response({'detail': 'Participant not found.'}, status=status.HTTP_404_NOT_FOUND)

        participant.delete()
        return Response({'detail': 'Participant deleted.'}, status=status.HTTP_204_NO_CONTENT)


# class PostShuffledListAPIView2(APIView):
#     def get(self, request, user):
#         # Filter posts by the specific user
#         posts = Post.objects.filter(user__id=user).order_by('?')  # or filter(user=user) if `user` is a ForeignKey
#         serializer = PostSerializer(posts, many=True, context={'user_id': user})
#         return Response(serializer.data, status=status.HTTP_200_OK)


class UserVideosAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        username = request.GET.get('username')

        if username:
            user = Register.objects.filter(user__username=username).first()
        else:
            user = get_object_or_404(Register, user=request.user.id)

        # Fetch all Participant instances for the given user with non-empty video fields
        # participants = Participant.objects.filter(user=user).exclude(file_uri__isnull=True)
        participants = Participant.objects.filter(user=user, video__isnull=False).exclude(video="")
        print('participants>>>', participants)

        participants_serializer = ParticipantSerializer(participants, many=True, context={'user_id': request.user.id})

        return Response(participants_serializer.data, status=status.HTTP_200_OK)


class PostShuffledListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # try:
        value = request.query_params.get('value')
        print(f"DEBUG PostShuffledListAPIView: value={value}, today={today}")
        split_value = value.split('-')
        if split_value[0] == "COMP":
            competition_id = int(split_value[1])
            participants_video = Participant.objects.filter(
                competition=competition_id,
                competition__start_date__lte=today,
                competition__end_date__gte=today,
                is_paid=True,  # Only show videos from paid participants
                video__isnull=False  # Only show participants with videos
            ).exclude(video="").order_by('?')
        elif split_value[0] == "TOUR":
            tournament_id = split_value[1]
            participants_video = Participant.objects.filter(
                tournament=tournament_id,
                competition__start_date__lte=today,
                competition__end_date__gte=today,
                is_paid=True,  # Only show videos from paid participants
                video__isnull=False  # Only show participants with videos
            ).exclude(video="").order_by('?')
        elif split_value[0] == "ALL":
            participants_video = Participant.objects.filter(
                competition__isnull=False,
                competition__start_date__lte=today,
                competition__end_date__gte=today,
                is_paid=True,  # Only show videos from paid participants
                video__isnull=False  # Only show participants with videos
            ).exclude(video="").order_by('?')

        else:
            return Response({'detail': 'query params not found'}, status=status.HTTP_404_NOT_FOUND)

        print(f"DEBUG PostShuffledListAPIView: Found {participants_video.count()} participants")
        serializer = ParticipantSerializer(participants_video, many=True, context={'user_id': request.user.id})
        print(f"DEBUG PostShuffledListAPIView: Serialized {len(serializer.data)} items")
        return Response(serializer.data, status=status.HTTP_200_OK)
    # except Exception as err:
    #     print('Error:', err)
    #     return Response({"detail": "An error occurred while fetching the participants."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.user.id
        post_id = request.data.get('post_id')
        post = get_object_or_404(Participant, id=post_id)
        user_register = get_object_or_404(Register, user=user_id)
        like, created = Like.objects.get_or_create(user=user_register, post=post)
        
        # Get the video owner (the person who posted the video)
        video_owner = post.user  # This is the Register object of the video owner
        
        if not created:
            # Unlike: Remove the like and decrease video owner's votes
            like.delete()
            video_owner.votes = max(video_owner.votes - 1, 0)
            video_owner.save()
            return Response({"message": "Post unliked"}, status=status.HTTP_200_OK)
        
        # Like: Add the like and increase video owner's votes
        video_owner.votes += 1
        video_owner.save()
        return Response({"message": "Post liked"}, status=status.HTTP_200_OK)


class CommentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        register = Register.objects.filter(user=request.user).first()
        request.data['user'] = register.id
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LikeDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class LikeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        if not post_id:
            return Response({'error': 'Post not found!'}, status=status.HTTP_404_NOT_FOUND)
        likes = Like.objects.filter(post__id=post_id)
        serializer = LikeSerializer(likes, many=True)
        print(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        if not post_id:
            return Response({'error': 'Post not found!'}, status=status.HTTP_404_NOT_FOUND)
        comments = Comment.objects.filter(post__id=post_id)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FavoriteListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class FavoriteDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ShareListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Share.objects.all()
    serializer_class = ShareSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ShareDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Share.objects.all()
    serializer_class = ShareSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class MergeVideoAndMusic(APIView):
    @staticmethod
    def cleanup_files(video_path, music_path):
        """Asynchronous cleanup of temporary files."""
        try:
            video_path = os.path.join('media', video_path)
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(music_path):
                os.remove(music_path)
        except Exception as e:
            print(f"Failed to delete temporary files: {str(e)}")

    def post(self, request):
        video_file = request.FILES.get('video')
        music_url = request.data.get('music')
        competition_id = request.data.get('competition_id')

        if not video_file or not music_url or not competition_id:
            return Response({"error": "Video file, music URL, and competition ID are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        register = Register.objects.filter(user=request.user).first()
        competition = Competition.objects.filter(id=competition_id).first()
        if not register or not competition:
            return Response({"error": "User or competition not found."},
                            status=status.HTTP_404_NOT_FOUND)

        # os.makedirs('media', exist_ok=True)
        # os.makedirs('media/temp_videos', exist_ok=True)
        temp_video_dir = os.path.join('media', 'temp_videos')
        os.makedirs(temp_video_dir, exist_ok=True)
        video_file_extension = video_file.name.split('.')[-1]
        video_filename = f"{request.user.username}_{uuid.uuid4().hex}.{video_file_extension}"
        video_path = default_storage.save(os.path.join('temp_videos', video_filename), video_file)

        if video_file.size > 40 * 1024 * 1024:
            return Response({"error": "Video file must be 50MB or less."}, status=400)

        video_path = os.path.join('media', video_path)
        # if video_file.size > 15 * 1024 * 1024:
        os.makedirs(os.path.join('media', 'competition_participants_temp_videos'), exist_ok=True)
        output_path = os.path.join('media', 'competition_participants_temp_videos',
                                    f"{request.user.username}_{uuid.uuid4().hex}.{video_file.name.split('.')[-1]}")
        compress_status = compressVideo(video_path, output_path)
        if not compress_status:
            return Response({'detail': 'Something went wrong..'}, status=status.HTTP_400_BAD_REQUEST)
        # else:
        #     output_path = video_path

        # Download the music file from the URL
        music_path = os.path.join('media', f"{uuid.uuid4().hex}.mp3")
        try:
            with requests.get(music_url, stream=True) as r:
                r.raise_for_status()
                with open(music_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        except requests.RequestException:
            return Response({"error": "Something went wrong, please try again!"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Merge video and music
        print('output_path>>>', output_path)
        try:
            # Simple video processing without moviepy
            # Just use the compressed video without merging audio
            merged_video_name = f"{request.user.username}_{uuid.uuid4().hex}.mp4"
            final_output_path = os.path.join('media', "merged_videos", merged_video_name)
            os.makedirs(os.path.dirname(final_output_path), exist_ok=True)
            
            # Copy the compressed video to the final location
            import shutil
            shutil.copy2(output_path, final_output_path)

            participant, _ = Participant.objects.get_or_create(user=register, competition=competition)
            azure_video_path = f"competition_participants_videos/{uuid.uuid4().hex}.{merged_video_name.split('.')[-1]}"

            with open(final_output_path, "rb") as f:
                django_file = File(f)
                participant.video.save(azure_video_path, django_file, save=False)
                participant.file_uri = f"{settings.DOMAIN_URL}/{azure_video_path}"
                participant.temp_video = final_output_path
                participant.save()

        except Exception as e:
            print(e, '---------')
            return Response({"error": f"Something went wrong, please try again!"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            # Clean up temporary files
            cleanup_thread = threading.Thread(target=self.cleanup_files, args=(video_path, music_path))
            cleanup_thread.start()

        # Return the path to the processed video
        return Response({"merged_video": f"media/merged_videos/{merged_video_name}"},
                        status=status.HTTP_200_OK)


class RemoveTempVideo(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        competition_id = request.data.get('competition_id')
        if not competition_id:
            return Response({"error": "Competition not found!"},
                            status=status.HTTP_404_NOT_FOUND)
        register = Register.objects.filter(user=request.user).first()
        participant = Participant.objects.filter(competition=competition_id, user=register).first()
        if not participant:
            return Response({"error": "Participant not found!"},
                            status=status.HTTP_404_NOT_FOUND)
        participant.delete()
        return Response(status=status.HTTP_200_OK)


class DeleteParticipantAPIView(APIView):
    """
    Delete Participant API
    
    Deletes the authenticated user's participation from a specific competition.
    Also cleans up associated video files.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Delete authenticated user's participation from a competition",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['competition_id'],
            properties={
                'competition_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID of the competition to remove participation from'
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Participant deleted successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                        'deleted_participant': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'competition_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'username': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(description="Missing competition_id parameter"),
            404: openapi.Response(description="Participant, competition, or user registration not found")
        },
        tags=['Participants']
    )
    def delete(self, request):
        competition_id = request.data.get('competition_id')
        
        # Validate required parameter
        if not competition_id:
            return Response(
                {"error": "competition_id is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get the competition
            competition = Competition.objects.get(id=competition_id)
        except Competition.DoesNotExist:
            return Response(
                {"error": "Competition not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get current user's register instance (user ID from token)
        current_register = Register.objects.filter(user=request.user).first()
        if not current_register:
            return Response(
                {"error": "User registration not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Find the participant for the authenticated user
            participant = Participant.objects.get(
                competition=competition, 
                user=current_register
            )
        except Participant.DoesNotExist:
            return Response(
                {"error": "You are not participating in this competition."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Store participant info before deletion
        participant_info = {
            'id': participant.id,
            'competition_id': competition.id,
            'username': current_register.user.username
        }
        
        # Clean up video files before deletion
        try:
            participant.cleanup_video_files()
        except Exception as e:
            print(f"Error during video cleanup: {e}")
            # Continue with deletion even if cleanup fails
        
        # Delete the participant
        participant.delete()
        
        return Response({
            "message": "Your participation has been removed successfully.",
            "deleted_participant": participant_info
        }, status=status.HTTP_200_OK)


class RecoverParticipantVideosAPIView(APIView):
    """
    Recovery API to fix participants with missing video files
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Attempt to recover missing video files for participants"""
        try:
            recovery_results = {
                'total_participants': 0,
                'participants_with_missing_files': 0,
                'recovery_attempts': 0,
                'successful_recoveries': 0,
                'failed_recoveries': 0,
                'details': []
            }
            
            # Find all participants
            all_participants = Participant.objects.all()
            recovery_results['total_participants'] = all_participants.count()
            
            media_dir = os.path.join(settings.MEDIA_ROOT, 'competition_participants_videos')
            
            # Get all files in media directory
            available_files = []
            if os.path.exists(media_dir):
                available_files = [f for f in os.listdir(media_dir) if os.path.isfile(os.path.join(media_dir, f))]
            
            for participant in all_participants:
                participant_detail = {
                    'participant_id': participant.id,
                    'username': participant.user.user.username,
                    'status': 'ok'
                }
                
                # Check if main video file exists
                if participant.video:
                    try:
                        video_path = participant.video.path
                        if not os.path.exists(video_path):
                            recovery_results['participants_with_missing_files'] += 1
                            participant_detail['status'] = 'missing_main_video'
                            participant_detail['expected_path'] = video_path
                            
                            # Try to find a matching file
                            username = participant.user.user.username
                            matching_files = [f for f in available_files if username.lower() in f.lower()]
                            
                            if matching_files:
                                recovery_results['recovery_attempts'] += 1
                                # Use the first matching file
                                source_file = os.path.join(media_dir, matching_files[0])
                                
                                try:
                                    # Copy the file to the expected location
                                    import shutil
                                    os.makedirs(os.path.dirname(video_path), exist_ok=True)
                                    shutil.copy2(source_file, video_path)
                                    
                                    participant_detail['status'] = 'recovered'
                                    participant_detail['recovered_from'] = matching_files[0]
                                    recovery_results['successful_recoveries'] += 1
                                    
                                except Exception as recover_err:
                                    participant_detail['status'] = 'recovery_failed'
                                    participant_detail['error'] = str(recover_err)
                                    recovery_results['failed_recoveries'] += 1
                            else:
                                participant_detail['status'] = 'no_matching_files'
                                participant_detail['available_files'] = matching_files
                                
                    except Exception as e:
                        participant_detail['status'] = 'error_checking'
                        participant_detail['error'] = str(e)
                
                # Check temp video
                if participant.temp_video:
                    try:
                        temp_path = participant.temp_video.path
                        participant_detail['temp_video_exists'] = os.path.exists(temp_path)
                    except:
                        participant_detail['temp_video_exists'] = False
                
                recovery_results['details'].append(participant_detail)
            
            return Response(recovery_results, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            return Response({
                'error': f'Recovery API error: {str(e)}',
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductionMediaCheckAPIView(APIView):
    """
    Check production media directory permissions and setup
    """
    
    def get(self, request):
        """Check production environment media setup"""
        try:
            media_root = settings.MEDIA_ROOT
            media_dir = os.path.join(media_root, 'competition_participants_videos')
            
            check_results = {
                'media_root': media_root,
                'media_root_exists': os.path.exists(media_root),
                'competition_dir': media_dir,
                'competition_dir_exists': os.path.exists(media_dir),
                'permissions_check': {},
                'directory_creation_test': {},
                'file_write_test': {},
                'environment_info': {}
            }
            
            # Environment info
            check_results['environment_info'] = {
                'debug_mode': settings.DEBUG,
                'current_working_directory': os.getcwd(),
                'process_id': os.getpid(),
            }
            
            # Check if we're on Linux/Unix (production)
            try:
                import pwd
                import grp
                import stat
                
                # Get current process user info
                current_uid = os.getuid()
                current_gid = os.getgid()
                check_results['environment_info'].update({
                    'current_user_id': current_uid,
                    'current_group_id': current_gid,
                    'current_user_name': pwd.getpwuid(current_uid).pw_name,
                    'current_group_name': grp.getgrgid(current_gid).gr_name,
                    'platform': 'unix'
                })
                
                # Check permissions for directories
                for path, name in [(media_root, 'media_root'), (media_dir, 'competition_dir')]:
                    if os.path.exists(path):
                        stat_info = os.stat(path)
                        owner = pwd.getpwuid(stat_info.st_uid).pw_name
                        group = grp.getgrgid(stat_info.st_gid).gr_name
                        
                        check_results['permissions_check'][name] = {
                            'path': path,
                            'owner': owner,
                            'group': group,
                            'permissions_octal': oct(stat_info.st_mode)[-3:],
                            'permissions_readable': stat.S_IMODE(stat_info.st_mode),
                            'readable': os.access(path, os.R_OK),
                            'writable': os.access(path, os.W_OK),
                            'executable': os.access(path, os.X_OK)
                        }
                    else:
                        check_results['permissions_check'][name] = {
                            'path': path,
                            'exists': False,
                            'error': 'Directory does not exist'
                        }
                        
            except ImportError:
                # Windows environment
                check_results['environment_info']['platform'] = 'windows'
                for path, name in [(media_root, 'media_root'), (media_dir, 'competition_dir')]:
                    if os.path.exists(path):
                        check_results['permissions_check'][name] = {
                            'path': path,
                            'readable': os.access(path, os.R_OK),
                            'writable': os.access(path, os.W_OK),
                            'executable': os.access(path, os.X_OK)
                        }
            
            # Test directory creation
            try:
                if not os.path.exists(media_dir):
                    os.makedirs(media_dir, mode=0o755, exist_ok=True)
                    check_results['directory_creation_test']['created_media_dir'] = True
                
                test_dir = os.path.join(media_dir, 'test_dir_permissions')
                os.makedirs(test_dir, mode=0o755, exist_ok=True)
                
                check_results['directory_creation_test'] = {
                    'success': True,
                    'test_dir': test_dir,
                    'exists_after_creation': os.path.exists(test_dir)
                }
                
                # Clean up test directory
                if os.path.exists(test_dir):
                    os.rmdir(test_dir)
                    
            except Exception as e:
                check_results['directory_creation_test'] = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            
            # Test file writing
            try:
                # Ensure directory exists first
                os.makedirs(media_dir, mode=0o755, exist_ok=True)
                
                test_file_path = os.path.join(media_dir, 'test_write_permissions.txt')
                test_content = 'Test file write permissions'
                
                with open(test_file_path, 'w') as f:
                    f.write(test_content)
                
                # Verify file was written
                file_exists = os.path.exists(test_file_path)
                file_size = os.path.getsize(test_file_path) if file_exists else 0
                
                # Read back the content
                read_content = ''
                if file_exists:
                    with open(test_file_path, 'r') as f:
                        read_content = f.read()
                
                check_results['file_write_test'] = {
                    'success': True,
                    'test_file_path': test_file_path,
                    'file_exists': file_exists,
                    'file_size': file_size,
                    'content_matches': read_content == test_content
                }
                
                # Clean up test file
                if os.path.exists(test_file_path):
                    os.remove(test_file_path)
                    
            except Exception as e:
                check_results['file_write_test'] = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            
            return Response(check_results, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            return Response({
                'error': f'Production media check failed: {str(e)}',
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MediaDebugAPIView(APIView):
    """
    Debug API to check media directory and file system
    """
    
    def get(self, request):
        """Get media directory information for debugging"""
        try:
            media_root = settings.MEDIA_ROOT
            media_dir = os.path.join(media_root, 'competition_participants_videos')
            
            debug_info = {
                'media_root': media_root,
                'media_root_exists': os.path.exists(media_root),
                'competition_videos_dir': media_dir,
                'competition_videos_dir_exists': os.path.exists(media_dir),
                'files_in_media_root': [],
                'files_in_competition_dir': [],
                'total_participants': 0,
                'participants_with_temp_video': 0,
                'participants_with_main_video': 0,
                'recent_participants': [],
                'all_participants': []
            }
            
            # List files in media root
            if os.path.exists(media_root):
                try:
                    debug_info['files_in_media_root'] = os.listdir(media_root)
                except Exception as e:
                    debug_info['media_root_error'] = str(e)
            
            # List files in competition videos directory
            if os.path.exists(media_dir):
                try:
                    files = os.listdir(media_dir)
                    debug_info['files_in_competition_dir'] = files[:20]  # Limit to first 20
                    debug_info['file_count'] = len(files)
                    
                    # Get file sizes
                    for file in files[:10]:  # First 10 files with sizes
                        file_path = os.path.join(media_dir, file)
                        if os.path.isfile(file_path):
                            size = os.path.getsize(file_path)
                            debug_info['files_in_competition_dir'].append(f"{file} ({size} bytes)")
                        
                except Exception as e:
                    debug_info['competition_dir_error'] = str(e)
            
            # Database checks
            try:
                debug_info['total_participants'] = Participant.objects.count()
                
                debug_info['participants_with_temp_video'] = Participant.objects.filter(
                    temp_video__isnull=False
                ).exclude(temp_video="").count()
                
                debug_info['participants_with_main_video'] = Participant.objects.filter(
                    video__isnull=False
                ).exclude(video="").count()
                
                # Get ALL participants (not just with temp_video)
                all_participants = Participant.objects.all().order_by('-id')[:10]
                
                for participant in all_participants:
                    p_info = {
                        'id': participant.id,
                        'user': participant.user.user.username,
                        'competition_id': participant.competition.id if participant.competition else None,
                        'competition_name': participant.competition.name if participant.competition else None,
                        'is_paid': participant.is_paid,
                        'video': str(participant.video) if participant.video else None,
                        'temp_video': str(participant.temp_video) if participant.temp_video else None,
                        'file_uri': participant.file_uri,
                    }
                    
                    # Check if files exist
                    if participant.temp_video:
                        try:
                            p_info['temp_video_path'] = participant.temp_video.path
                            p_info['temp_video_exists'] = os.path.exists(participant.temp_video.path)
                        except:
                            p_info['temp_video_path'] = 'Error getting path'
                            p_info['temp_video_exists'] = False
                    
                    if participant.video:
                        try:
                            p_info['video_path'] = participant.video.path
                            p_info['video_exists'] = os.path.exists(participant.video.path)
                        except:
                            p_info['video_path'] = 'Error getting path'
                            p_info['video_exists'] = False
                    
                    debug_info['all_participants'].append(p_info)
                
            except Exception as e:
                debug_info['database_error'] = str(e)
            
            return Response(debug_info, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            return Response({
                'error': f'Debug API error: {str(e)}',
                'traceback': traceback.format_exc()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ActiveCompetitionVideosAPIView(APIView):
    """
    Active Competition Videos API
    
    Returns all videos from competitions that are currently active (between start and end dates).
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get all videos from competitions that are currently active",
        manual_parameters=[
            openapi.Parameter(
                'shuffle',
                openapi.IN_QUERY,
                description="Whether to shuffle the results (default: true)",
                type=openapi.TYPE_BOOLEAN,
                required=False
            ),
            openapi.Parameter(
                'paid_only',
                openapi.IN_QUERY,
                description="Whether to include only paid participants (default: true)",
                type=openapi.TYPE_BOOLEAN,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="List of videos from active competitions",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of videos'),
                        'active_competitions_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of active competitions'),
                        'videos': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=ParticipantSerializer
                        )
                    }
                )
            )
        },
        tags=['Videos']
    )
    def get(self, request):
        from django.utils import timezone
        today = timezone.now()
        
        # Get query parameters
        shuffle = request.query_params.get('shuffle', 'true').lower() == 'true'
        paid_only = request.query_params.get('paid_only', 'true').lower() == 'true'
        
        print(f"DEBUG ActiveCompetitionVideosAPIView: shuffle={shuffle}, paid_only={paid_only}, today={today}")
        
        # Base query: get all participants with videos from competitions that are currently active
        queryset = Participant.objects.filter(
            competition__isnull=False,  # Has a competition
            competition__start_date__lte=today,  # Competition has started
            competition__end_date__gte=today,   # Competition hasn't ended
            video__isnull=False  # Has a video
        ).exclude(video="")  # Video field is not empty
        
        # Filter by paid participants if requested
        if paid_only:
            queryset = queryset.filter(is_paid=True)
        
        # Apply ordering
        if shuffle:
            queryset = queryset.order_by('?')  # Random order
        else:
            queryset = queryset.order_by('-id')  # Latest first
        
        # Get count of unique active competitions
        active_competitions = queryset.values_list('competition_id', flat=True).distinct()
        active_competitions_count = len(set(active_competitions))
        
        print(f"DEBUG ActiveCompetitionVideosAPIView: Found {queryset.count()} videos from {active_competitions_count} active competitions")
        
        # Serialize the data
        serializer = ParticipantSerializer(queryset, many=True, context={'user_id': request.user.id})
        
        return Response({
            'count': queryset.count(),
            'active_competitions_count': active_competitions_count,
            'videos': serializer.data
        }, status=status.HTTP_200_OK)


class CompetitionDetailForUserAPIView(APIView):
    """
    Competition Detail API for Authenticated User
    
    Gets competition details along with the authenticated user's participation status.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get competition details with user participation status",
        manual_parameters=[
            openapi.Parameter(
                'competition_id',
                openapi.IN_PATH,
                description="Competition ID",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Competition details with user participation info",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'competition': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Competition details'
                        ),
                        'user_participation': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'is_participating': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'participant_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'is_paid': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'has_video': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                'video_url': openapi.Schema(type=openapi.TYPE_STRING),
                                'submission_date': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        ),
                        'statistics': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'total_participants': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'paid_participants': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'remaining_slots': openapi.Schema(type=openapi.TYPE_INTEGER)
                            }
                        )
                    }
                )
            ),
            404: openapi.Response(description="Competition not found")
        },
        tags=['Competitions']
    )
    def get(self, request, competition_id):
        try:
            # Get the competition
            competition = Competition.objects.get(id=competition_id)
        except Competition.DoesNotExist:
            return Response(
                {"error": "Competition not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get current user's register instance
        current_register = Register.objects.filter(user=request.user).first()
        if not current_register:
            return Response(
                {"error": "User registration not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get user's participation details
        participant = Participant.objects.filter(
            competition=competition, 
            user=current_register
        ).first()
        
        # Serialize competition data with user context
        from dashboard.serializers import CompetitionSerializer
        competition_serializer = CompetitionSerializer(
            competition, 
            context={'user_id': request.user.id}
        )
        
        # Prepare user participation data
        user_participation = {
            'is_participating': bool(participant),
            'participant_id': participant.id if participant else None,
            'is_paid': participant.is_paid if participant else False,
            'has_video': bool(participant and (participant.video or participant.temp_video)) if participant else False,
            'video_url': None,
            'submission_date': None
        }
        
        if participant:
            # Get video URL
            if participant.video:
                user_participation['video_url'] = participant.video.url
            elif participant.file_uri:
                user_participation['video_url'] = participant.file_uri
            
            # Get submission date (when participant was created/last updated)
            user_participation['submission_date'] = participant.updated_at or participant.created_at if hasattr(participant, 'updated_at') else None
        
        # Get competition statistics
        all_participants = Participant.objects.filter(competition=competition)
        paid_participants = all_participants.filter(is_paid=True)
        
        statistics = {
            'total_participants': all_participants.count(),
            'paid_participants': paid_participants.count(),
            'remaining_slots': max(0, competition.max_participants - paid_participants.count()) if competition.max_participants else None
        }
        
        return Response({
            'competition': competition_serializer.data,
            'user_participation': user_participation,
            'statistics': statistics
        }, status=status.HTTP_200_OK)


def compressVideo(video_path, output_path):
    print('Input:', video_path, 'Output:', output_path)
    command = [
        'ffmpeg', '-i', video_path, 
        '-vcodec', 'libx264', 
        '-crf', '28', 
        '-preset', 'fast',  # Changed from 'slow' to 'fast' for quicker processing
        '-movflags', '+faststart',  # Optimize for streaming
        '-y',  # Overwrite output file if exists
        output_path
    ]
    try:
        # Add timeout to prevent hanging
        subprocess.run(command, check=True, timeout=120)  # 2-minute timeout
        return True
    except subprocess.TimeoutExpired:
        print('Compression timeout - taking too long')
        return False
    except subprocess.CalledProcessError as err:
        print('1Compress Error:', err)
        return False
    except Exception as err:
        print('2Compress Error:', err)
        return False


class ParticipantTempSave(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        competition_id = request.data.get('competition')
        video = request.FILES.get('video')
        print("DEBUG: Starting ParticipantTempSave post method")
        print(f"DEBUG: competition_id = {competition_id}, video = {video}")
        print(f"DEBUG: MEDIA_ROOT = {settings.MEDIA_ROOT}")
        
        if not video:
            print("DEBUG: No video file provided")
            return Response({"error": "Video file is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not competition_id:
            print("DEBUG: No competition_id provided")
            return Response({"error": "Competition ID is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        print("DEBUG: Video and competition_id validated")
        print(f"DEBUG: Video size = {video.size} bytes")
        print(f"DEBUG: Video name = {video.name}")
        
        if video.size > 40 * 1024 * 1024:
            print("DEBUG: Video file too large")
            return Response({"error": "Video file must be 40MB or less."}, status=status.HTTP_400_BAD_REQUEST)

        print("DEBUG: Video size validation passed")
        # Check if the competition exists
        competition = Competition.objects.filter(id=competition_id).first()
        if not competition:
            return Response({'detail': 'Competition not found.'}, status=status.HTTP_404_NOT_FOUND)

        print("DEBUG: Competition found")
        # Get the registered user
        register = Register.objects.filter(user=request.user).first()
        if not register:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        print("DEBUG: User registration found")
        
        # Check if user is already a participant in this competition
        existing_participant = Participant.objects.filter(competition=competition, user=register).first()
        
        if existing_participant:
            # If participant exists and has already paid, don't allow new upload
            if existing_participant.is_paid:
                return Response({
                    "error": "You are already enrolled in this competition."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # If participant exists but hasn't paid, delete the old entry
            print(f"DEBUG: Deleting existing unpaid participant {existing_participant.id}")
            try:
                # DON'T clean up video files automatically - they might be referenced by other participants
                # or needed for recovery. Only delete the database record.
                print("DEBUG: Skipping automatic video file cleanup to prevent data loss")
                
                # Note: Uncomment below if you want aggressive cleanup (not recommended)
                # if hasattr(existing_participant, 'cleanup_video_files') and callable(existing_participant.cleanup_video_files):
                #     try:
                #         existing_participant.cleanup_video_files()
                #     except Exception as cleanup_err:
                #         print(f"DEBUG: cleanup_video_files failed: {cleanup_err}")
                # else:
                #     print("DEBUG: cleanup_video_files method not found on Participant instance")

                existing_participant.delete()
                print("DEBUG: Old unpaid participant entry deleted successfully")
            except Exception as e:
                print(f"DEBUG: Error deleting old participant: {e}")
                return Response({
                    "error": "Error removing previous entry. Please try again."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create new participant entry
        try:
            from django.db import transaction
            with transaction.atomic():
                participant = Participant.objects.create(competition=competition, user=register)
                print(f"DEBUG: New participant created with ID: {participant.id}")
                print(f"DEBUG: Participant exists in DB: {Participant.objects.filter(id=participant.id).exists()}")
        except Exception as e:
            print(f"DEBUG: Error creating participant: {e}")
            print(f"DEBUG: Exception type: {type(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return Response({'detail': f'Error creating participant entry: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ensure media directories exist
            media_dir = os.path.join(settings.MEDIA_ROOT, 'competition_participants_videos')
            os.makedirs(media_dir, exist_ok=True)
            print(f"DEBUG: Media directory ensured: {media_dir}")
            
            # Generate unique filename
            file_extension = video.name.split('.')[-1] if '.' in video.name else 'mp4'
            unique_filename = f"{request.user.username}_{uuid.uuid4().hex}.{file_extension}"
            
            # Save the uploaded video first
            temp_path = default_storage.save(
                f"competition_participants_videos/{unique_filename}", 
                video
            )
            full_temp_path = os.path.join(settings.MEDIA_ROOT, temp_path)
            print(f"DEBUG: Video saved temporarily to: {temp_path}")
            print(f"DEBUG: Full temp path: {full_temp_path}")
            print(f"DEBUG: File exists check: {os.path.exists(full_temp_path)}")

            # Determine output path
            if video.size > 15 * 1024 * 1024:
                # Compress for large videos
                compressed_filename = f"compressed_{uuid.uuid4().hex}.{file_extension}"
                output_path = os.path.join(settings.MEDIA_ROOT, "competition_participants_videos", compressed_filename)
                print(f"DEBUG: Starting compression for large video to: {output_path}")
                
                compress_status = compressVideo(full_temp_path, output_path)
                if not compress_status:
                    print("DEBUG: Compression failed")
                    return Response({'detail': 'Video compression failed.'}, status=status.HTTP_400_BAD_REQUEST)
                print("DEBUG: Compression completed successfully")
                print(f"DEBUG: Compressed file exists: {os.path.exists(output_path)}")
            else:
                # Use original file for small videos
                output_path = full_temp_path
                print("DEBUG: Using original file (small size)")
            
            print(f"DEBUG: Final output path: {output_path}")
            print(f"DEBUG: Output file exists: {os.path.exists(output_path)}")
            
        except Exception as e:
            print(f"DEBUG: Error during video processing: {e}")
            print(f"DEBUG: Error type: {type(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return Response({'detail': f'Error processing video file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Save the processed video to participant
            print(f"DEBUG: Attempting to save video to participant from: {output_path}")
            
            if not os.path.exists(output_path):
                print(f"DEBUG: ERROR - Output file does not exist: {output_path}")
                return Response({'detail': 'Processed video file not found.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get file size for verification
            file_size = os.path.getsize(output_path)
            print(f"DEBUG: File size to save: {file_size} bytes")
            
            with open(output_path, 'rb') as f:
                django_file = File(f)
                final_filename = os.path.basename(output_path)
                print(f"DEBUG: Saving with filename: {final_filename}")
                
                # Save to temp_video field
                participant.temp_video.save(final_filename, django_file, save=False)
                print(f"DEBUG: temp_video field saved: {participant.temp_video}")
                print(f"DEBUG: temp_video path: {participant.temp_video.path if participant.temp_video else 'None'}")
                
                participant.save()
                print("DEBUG: Participant model saved successfully")

            # Verify the file was saved
            if participant.temp_video:
                saved_path = participant.temp_video.path
                print(f"DEBUG: Final saved path: {saved_path}")
                print(f"DEBUG: Final file exists: {os.path.exists(saved_path)}")
            
            # Final verification
            print(f"DEBUG: Final verification - Participant ID: {participant.id}")
            print(f"DEBUG: Participant exists in DB after save: {Participant.objects.filter(id=participant.id).exists()}")
            
            # Check if the participant can be retrieved
            verification_participant = Participant.objects.filter(id=participant.id).first()
            if verification_participant:
                print(f"DEBUG: Verification - temp_video: {verification_participant.temp_video}")
                print(f"DEBUG: Verification - competition: {verification_participant.competition}")
                print(f"DEBUG: Verification - user: {verification_participant.user}")
            else:
                print(f"DEBUG: ERROR - Participant {participant.id} not found in database!")
            
            return Response({
                "message": "Video uploaded successfully",
                "participant_id": participant.id,
                "temp_video_path": str(participant.temp_video) if participant.temp_video else None,
                "file_uri": participant.file_uri,
                "debug_info": {
                    "participant_exists": Participant.objects.filter(id=participant.id).exists(),
                    "file_saved_path": saved_path if participant.temp_video else None,
                    "file_exists_on_disk": os.path.exists(saved_path) if participant.temp_video else False
                }
            }, status=status.HTTP_200_OK)
            
        except FileNotFoundError as e:
            print(f"DEBUG: Video file not found: {e}")
            return Response({'detail': 'Processed video file not found.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"DEBUG: Error saving participant video: {e}")
            print(f"DEBUG: Error type: {type(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            return Response({'detail': f'Error saving video to participant: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
