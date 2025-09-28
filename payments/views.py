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
    def post(self, request):
        try:
            competition = request.data.get('competition')
            tci = request.data.get('tci')
            serializer = PaymentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                register = Register.objects.filter(user=request.user).first()
                # if competition:
                if tci:
                    participant = Participant.objects.filter(user=register, competition__id=tci).first()
                else:
                    participant = Participant.objects.filter(user=register, competition__id=competition).first()
                # else:
                    # participant = Participant.objects.filter(user=register, tournament__id=tournament).first()
                # if not participant:
                #     return Response({'message': 'You are not registered for this competition'}, status=status.HTTP_400_BAD_REQUEST)

                participant.is_paid = True
                
                if participant.temp_video:
                    participant.video = participant.temp_video
                    print(participant.temp_video, "Deleting video from all locations...")
                    video_filename = os.path.basename(str(participant.temp_video)) 
                    # video_filename.split('_')
                    # video_filename = video_filename.split('_')[0]

                    for folder in MEDIA_FOLDERS:
                        folder_path = os.path.join("media", folder)  # Get full folder path
                        
                        if os.path.exists(folder_path):  # Check if the folder exists
                            for file in os.listdir(folder_path):  # Iterate through files in the folder
                                if request.user.username in file:  # Check if video_filename is a substring
                                    file_path = os.path.join(folder_path, file)
                                    os.remove(file_path)  # Delete the file
                                    print(f"Deleted: {file_path}")
                                else:
                                    print(f"Not matched:")
                    participant.temp_video = None
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



# this is test

