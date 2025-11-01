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
        participant.video = participant.temp_video
        participant.temp_video = None
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
        if not created:
            like.delete()
            user_register.votes = max(user_register.votes - 1, 0)
            user_register.save()
            return Response({"message": "Post unliked"}, status=status.HTTP_200_OK)
        user_register.votes += 1
        user_register.save()
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
        if not video or not competition_id:
            return Response({"error": "Video file and competition ID are required."},
                            status=status.HTTP_400_BAD_REQUEST)
        print("DEBUG: Video and competition_id validated")
        if video.size > 40 * 1024 * 1024:
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
                # Clean up old video files before deletion if method exists
                if hasattr(existing_participant, 'cleanup_video_files') and callable(existing_participant.cleanup_video_files):
                    try:
                        existing_participant.cleanup_video_files()
                    except Exception as cleanup_err:
                        # Log cleanup error but continue to attempt deletion
                        print(f"DEBUG: cleanup_video_files failed: {cleanup_err}")
                else:
                    print("DEBUG: cleanup_video_files method not found on Participant instance; skipping cleanup")

                existing_participant.delete()
                print("DEBUG: Old unpaid participant entry deleted successfully")
            except Exception as e:
                print(f"DEBUG: Error deleting old participant: {e}")
                return Response({
                    "error": "Error removing previous entry. Please try again."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create new participant entry
        participant = Participant.objects.create(competition=competition, user=register)
        print(f"DEBUG: New participant created with ID: {participant.id}")

        # Compress the video if it's larger than 15MB (stored in local storage temporarily)
        temp_path = default_storage.save(f"competition_participants_videos/{request.user.username}_{uuid.uuid4().hex}.{video.name.split('.')[-1]}", video)
        compress_input_path = os.path.join(settings.MEDIA_ROOT, temp_path)

        # Only compress if video is larger than 15MB
        if video.size > 15 * 1024 * 1024:
            output_path = os.path.join(settings.MEDIA_ROOT, "competition_participants_videos",
                                        f"{uuid.uuid4().hex}.{video.name.split('.')[-1]}")
            compress_status = compressVideo(compress_input_path, output_path)
            if not compress_status:
                return Response({'detail': 'Something went wrong during compression.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Use original file if it's small enough
            output_path = compress_input_path
        # else:
        #     output_path = compress_input_path

        # Upload the compressed video to Azure Blob Storage
        # azure_video_path = f"competition_participants_videos/{uuid.uuid4().hex}.{video.name.split('.')[-1]}"
        # upload_video_to_azure(output_path, azure_video_path)
        # with open(output_path, "rb") as f:
        #     azure_storage = AzureMediaStorage()
        #     azure_storage.save(azure_video_path, f)

        # participant.file_uri = f"{settings.AZURE_FRONT_DOOR_DOMAIN}/{azure_video_path}"

        with open(output_path, 'rb') as f:
            django_file = File(f)
            participant.temp_video.save(os.path.basename(output_path), django_file, save=True)

        # participant.temp_video = temp_path
        participant.save()

        return Response({
            "message": "Video uploaded successfully",
            "file_uri": participant.file_uri
        }, status=status.HTTP_200_OK)
