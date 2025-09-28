import random
from django.core.mail import send_mail
from django.conf import settings
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Register
from django.contrib.auth.models import User

CLIENT_ID = "528751908224-u4d7cuelmvmfsbv6qtsvlhki5ijccqgd.apps.googleusercontent.com"

# Function to generate a 6-digit OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# Function to send OTP via emailX
def send_otp(email, otp):
    subject = "Your OTP for Registration"
    print(otp, '==================')
    message = f"Your OTP for registration is {otp}. Please use this to complete your registration."
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)


def verify_google_token(token):
    try:
        # Verify the Google token
        id_info = id_token.verify_oauth2_token(token, Request(), CLIENT_ID)
        return id_info
    except ValueError:
        raise Exception("Invalid token")
    except Exception as er:
        print('Error:', er)
        raise Exception("Invalid token")