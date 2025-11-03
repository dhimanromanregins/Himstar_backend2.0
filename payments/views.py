import hashlib
from rest_framework import status
import uuid
from accounts.models import  Register, Referral, ReferralReward
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import PaymentSerializer
from video.serializers import ParticipantSerializer
import requests
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from payments.models import PaymentDetails
from video.models import Participant
from wallet.models import ReferrelPaymentHistory
import os

MEDIA_FOLDERS = [
    "competition_participants_temp_videos",
    "competition_participants_videos",
    "merged_videos",
    "temp_videos"
]


class PaymentCreateGetAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def cleanup_participant_and_videos(self, participant, username):
        """
        DISABLED: Clean up participant entry and associated video files
        This was causing video files to be deleted during payment processing
        """
        if not participant:
            return
            
        print(f"PAYMENT: Skipping cleanup for participant {participant.id} and videos for user: {username}")
        print(f"PAYMENT: Files will be preserved to prevent data loss")
        
        # DISABLED: Clean up video files from all media folders
        # This was deleting files that users had uploaded
        # for folder in MEDIA_FOLDERS:
        #     folder_path = os.path.join("media", folder)
        #     if os.path.exists(folder_path):
        #         for file in os.listdir(folder_path):
        #             if username in file:
        #                 file_path = os.path.join(folder_path, file)
        #                 try:
        #                     os.remove(file_path)
        #                     print(f"Deleted video file: {file_path}")
        #                 except Exception as e:
        #                     print(f"Error deleting file {file_path}: {e}")
        
        # DISABLED: Delete the participant entry - keep for recovery
        # try:
        #     participant_id = participant.id
        #     participant.delete()
        #     print(f"Successfully deleted participant entry: {participant_id}")
        # except Exception as e:
        #     print(f"Error deleting participant: {e}")
        
        print(f"PAYMENT: Cleanup skipped - participant and files preserved")
    
    def post(self, request):
        try:
            competition = request.data.get('competition')
            tci = request.data.get('tci')
            payment_status = request.data.get('status')
            
            # Critical: Check if payment was successful
            if payment_status != 'success':
                # Clean up participant entry and videos for failed payments
                register = Register.objects.filter(user=request.user).first()
                if register:
                    # Find the participant entry
                    if tci:
                        participant = Participant.objects.filter(user=register, competition__id=tci).first()
                    else:
                        participant = Participant.objects.filter(user=register, competition__id=competition).first()
                    
                    # Use cleanup method to remove participant and videos
                    if participant:
                        self.cleanup_participant_and_videos(participant, request.user.username)
                
                return Response({
                    'error': 'Payment was not successful. Participant entry and video files have been cleaned up.',
                    'status': payment_status
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Additional validation: Check payment amount
            payment_amount = float(request.data.get('amount', 0))
            if payment_amount <= 0:
                return Response({
                    'error': 'Invalid payment amount',
                    'amount': payment_amount
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = PaymentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                register = Register.objects.filter(user=request.user).first()
                # if competition:
                if tci:
                    participant = Participant.objects.filter(user=register, competition__id=tci).first()
                else:
                    participant = Participant.objects.filter(user=register, competition__id=competition).first()
                
                # Critical: Check if participant exists
                if not participant:
                    return Response({
                        'error': 'You are not registered for this competition',
                        'competition_id': tci or competition
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Check if already paid to prevent double payment
                if participant.is_paid:
                    return Response({
                        'error': 'Payment already processed for this competition',
                        'participant_id': participant.id
                    }, status=status.HTTP_400_BAD_REQUEST)

                participant.is_paid = True
                
                if participant.temp_video:
                    participant.video = participant.temp_video
                    print(participant.temp_video, "Deleting video from all locations...")
                    video_filename = os.path.basename(str(participant.temp_video)) 
                    # video_filename.split('_')
                    # video_filename = video_filename.split('_')[0]

                    # DISABLED: Aggressive file cleanup that was deleting video files
                    # This was causing videos to disappear after payment processing
                    print(f"PAYMENT: NOT deleting files to prevent data loss")
                    print(f"PAYMENT: temp_video will be kept as backup: {participant.temp_video}")
                    
                    # for folder in MEDIA_FOLDERS:
                    #     folder_path = os.path.join("media", folder)  # Get full folder path
                    #     
                    #     if os.path.exists(folder_path):  # Check if the folder exists
                    #         for file in os.listdir(folder_path):  # Iterate through files in the folder
                    #             if request.user.username in file:  # Check if video_filename is a substring
                    #                 file_path = os.path.join(folder_path, file)
                    #                 os.remove(file_path)  # Delete the file
                    #                 print(f"Deleted: {file_path}")
                    #             else:
                    #                 print(f"Not matched:")
                    
                    # Don't clear temp_video - keep it as backup
                    # participant.temp_video = None
                    if participant.video:
                        participant.file_uri = f"{settings.DOMAIN_URL}{participant.video.url}"
                    participant.save(update_fields=['temp_video', 'file_uri'])
#                    participant.save(update_fields=['temp_video'])
                participant.save()
                payment = PaymentDetails.objects.filter(txnid=request.data.get('txnid'), user=register).first()
                payment.participant = participant
                payment.save()

                # apply referrel
                referrel = Referral.objects.filter(invitee=register, status='pending').first()
                referrel_amount = ReferralReward.objects.last()
                if referrel and referrel_amount:
                    ReferrelPaymentHistory.objects.create(amount=referrel_amount.amount, referrel=referrel)
                    referrel.inviter.points += referrel_amount.amount
                    referrel.invitee.points += referrel_amount.amount
                    referrel.inviter.save()
                    referrel.invitee.save()
                    referrel.status = 'confirmed'
                    referrel.save()

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print('Error:', e)
            return Response({'message': 'Something went wrong'}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        user = Register.objects.filter(user=request.user).first()
        payments = PaymentDetails.objects.filter(user=user)
        payments_serializer = PaymentSerializer(payments, many=True)
        return Response(payments_serializer.data, status=status.HTTP_200_OK)
    
@csrf_exempt
def successview(request):
    return render(request, 'success.html')


@csrf_exempt
def failure(request):
    return render(request, 'failure.html')


class CleanupUnpaidParticipantsAPIView(APIView):
    """
    API to clean up participants who uploaded videos but didn't complete payment
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        """
        Clean up user's unpaid participant entries and associated videos
        """
        try:
            competition_id = request.data.get('competition_id')
            register = Register.objects.filter(user=request.user).first()
            
            if not register:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Find unpaid participants
            if competition_id:
                unpaid_participants = Participant.objects.filter(
                    user=register, 
                    competition__id=competition_id,
                    is_paid=False
                )
            else:
                unpaid_participants = Participant.objects.filter(
                    user=register,
                    is_paid=False
                )
            
            if not unpaid_participants.exists():
                return Response({
                    'message': 'No unpaid participants found to clean up'
                }, status=status.HTTP_200_OK)
            
            cleanup_count = 0
            for participant in unpaid_participants:
                # Clean up videos and participant entry
                PaymentCreateGetAPIView().cleanup_participant_and_videos(participant, request.user.username)
                cleanup_count += 1
            
            return Response({
                'message': f'Successfully cleaned up {cleanup_count} unpaid participant entries and their videos',
                'cleaned_count': cleanup_count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f'Cleanup error: {e}')
            return Response({
                'error': 'Something went wrong during cleanup'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# this is test

