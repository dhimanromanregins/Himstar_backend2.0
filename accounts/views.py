from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, OTPVerifySerializer,LoginSerializer,AwardsSerializer, RegisterSerializerPasswordUpdate, ReferralHistorySerializer
from .models import Register, Awards, OTP, Referral
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .utils import verify_google_token
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import generate_otp, send_otp
import requests
from django.core.files.base import ContentFile
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# View to handle registration and sending OTP
class RegisterView(APIView):
    """
    User Registration API
    
    Handles user registration process and sends OTP for email verification.
    Validates user input, checks for duplicate entries, and validates referral codes.
    """
    
    @swagger_auto_schema(
        operation_description="Register a new user and send OTP for email verification",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'email', 'phonenumber', 'password', 'confirm_password', 'fullName', 'zipcode', 'gender', 'dob'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Unique username'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='User email address'),
                'phonenumber': openapi.Schema(type=openapi.TYPE_STRING, description='User phone number'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description='User password'),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description='Password confirmation'),
                'fullName': openapi.Schema(type=openapi.TYPE_STRING, description='User full name'),
                'zipcode': openapi.Schema(type=openapi.TYPE_STRING, description='User zipcode'),
                'gender': openapi.Schema(type=openapi.TYPE_STRING, enum=['male', 'female', 'other'], description='User gender'),
                'dob': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Date of birth (YYYY-MM-DD)'),
                'ref_code': openapi.Schema(type=openapi.TYPE_STRING, description='Optional referral code'),
            }
        ),
        responses={
            200: openapi.Response(
                description="OTP sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='HTTP status code'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                    }
                )
            ),
            400: openapi.Response(
                description="Validation errors",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
                        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username error'),
                        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email error'),
                        'phonenumber': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number error'),
                        'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password error'),
                    }
                )
            )
        },
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        print('request.data>>>', request.data)
        if User.objects.filter(username=request.data['username']).exists():
            return Response({"username": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=request.data['email']).exists():
            return Response({"email": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        if Register.objects.filter(phonenumber=request.data['phonenumber']).exists():
            return Response({"phonenumber": "Phone number already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        if request.data['password'] != request.data['confirm_password']:
            return Response({"password": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

        ref_code = request.data.get('ref_code')
        if ref_code:
            if len(ref_code) != 11 or ref_code[:3] != 'REF':
                return Response({"error": "Invalid referral code format."}, status=status.HTTP_400_BAD_REQUEST)
            inviter = Register.objects.filter(referral_code=ref_code).first()
            if not inviter:
                return Response({"error": "Referral code does not exist or is invalid."}, status=status.HTTP_400_BAD_REQUEST)

        otp_code = generate_otp()
        OTP.objects.update_or_create(email=request.data['email'], defaults={'otp': otp_code})
        send_otp(request.data['email'], otp_code)

        return Response({"status":status.HTTP_200_OK, "message": "OTP sent successfully"}, status=status.HTTP_200_OK)

class RegisterDetailAPIView(APIView):
    """
    User Profile Management API
    
    Handles retrieving and updating user profile information.
    Requires authentication for all operations.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get user profile details",
        manual_parameters=[
            openapi.Parameter(
                'username',
                openapi.IN_QUERY,
                description="Username to fetch profile (optional, defaults to current user)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={
            200: openapi.Response(
                description="User profile data",
                schema=RegisterSerializer
            ),
            404: openapi.Response(description="User not found")
        },
        tags=['User Profile']
    )
    def get(self, request):
        username = request.GET.get('username')
        if username:
            register = Register.objects.filter(user__username=username).first()
        else:    
            register = Register.objects.filter(user__id=request.user.id).first()

        if not register:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = RegisterSerializer(register, context={'user_id': register.id})
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @swagger_auto_schema(
        operation_description="Update user profile information",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description='New password'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
                'phonenumber': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
                'zipcode': openapi.Schema(type=openapi.TYPE_STRING, description='Zipcode'),
                'gender': openapi.Schema(type=openapi.TYPE_STRING, enum=['male', 'female', 'other'], description='Gender'),
                'dob': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Date of birth'),
                'profile_image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY, description='Profile image'),
                'cover_image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY, description='Cover image'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                schema=RegisterSerializerPasswordUpdate
            ),
            400: openapi.Response(description="Validation errors"),
            404: openapi.Response(description="User not found")
        },
        tags=['User Profile']
    )
    def patch(self, request):
        user_id = request.user.id
        register = get_object_or_404(Register, user_id=user_id)
        password = request.data.get('password')
        if password:
            register.user.set_password(password)
        print(request.data)

        # update user name
        fname = request.data.get('first_name')
        lname = request.data.get('last_name')
        if fname:
            register.user.first_name = fname
        if lname:
            register.user.last_name = lname

        serializer = RegisterSerializerPasswordUpdate(register, data=request.data, partial=True)
        if serializer.is_valid():
            register.user.save()
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPAndRegisterView(APIView):
    """
    OTP Verification and User Registration API
    
    Verifies the OTP sent during registration and completes the user registration process.
    """
    
    @swagger_auto_schema(
        operation_description="Verify OTP and complete user registration",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'otp', 'user_data'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='User email address'),
                'otp': openapi.Schema(type=openapi.TYPE_STRING, description='6-digit OTP code'),
                'user_data': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='Original user registration data',
                    properties={
                        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                        'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                        'fullName': openapi.Schema(type=openapi.TYPE_STRING, description='Full name'),
                        'phonenumber': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
                        'zipcode': openapi.Schema(type=openapi.TYPE_STRING, description='Zipcode'),
                        'gender': openapi.Schema(type=openapi.TYPE_STRING, enum=['male', 'female', 'other'], description='Gender'),
                        'dob': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Date of birth'),
                        'ref_code': openapi.Schema(type=openapi.TYPE_STRING, description='Referral code'),
                    }
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="User registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='HTTP status code'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message'),
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid OTP or validation errors",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
                    }
                )
            )
        },
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        otp_data = {
            "email": request.data.get('email'),
            "otp": request.data.get('otp')
        }
        user_data = request.data.get('user_data')  # user_data contains the original user data

        otp_serializer = OTPVerifySerializer(data=otp_data, context={'user_data': user_data})
        if otp_serializer.is_valid():
            otp_serializer.save()  # Register the user
            return Response({"status":status.HTTP_200_OK, "message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(otp_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    User Login API
    
    Authenticates users using username/email and password, returns JWT tokens.
    """
    
    @swagger_auto_schema(
        operation_description="Login user with username/email and password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username_or_email', 'password'],
            properties={
                'username_or_email': openapi.Schema(type=openapi.TYPE_STRING, description='Username or email address'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description='User password'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='HTTP status code'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
                        'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                        'reg_user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Register user ID'),
                        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
                        'phone': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Full name'),
                        'profile_image': openapi.Schema(type=openapi.TYPE_STRING, description='Profile image URL'),
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid credentials",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
                    }
                )
            )
        },
        tags=['Authentication']
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            tokens = serializer.get_tokens(user)
            register = Register.objects.filter(user__id=user.id).first()
            return Response({
                "status":status.HTTP_200_OK,
                'refresh': tokens['refresh'],
                'access': tokens['access'],
                'user_id': user.id,
                'reg_user_id': register.id,
                'username': user.username,
                'email': user.email,
                'phone': register.phonenumber,
                'name': f'{user.first_name} {user.last_name}',
                'profile_image': register.profile_image_url,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class AwardsAPIView(APIView):
    """
    Awards Management API
    
    Handles CRUD operations for awards in the system.
    """
    
    @swagger_auto_schema(
        operation_description="Get all awards",
        responses={
            200: openapi.Response(
                description="List of all awards",
                schema=AwardsSerializer(many=True)
            )
        },
        tags=['Awards']
    )
    def get(self, request):
        awards = Awards.objects.all()
        serializer = AwardsSerializer(awards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Create a new award",
        request_body=AwardsSerializer,
        responses={
            201: openapi.Response(
                description="Award created successfully",
                schema=AwardsSerializer
            ),
            400: openapi.Response(description="Validation errors")
        },
        tags=['Awards']
    )
    def post(self, request):
        serializer = AwardsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class GoogleLoginView(APIView):
    """
    Google OAuth Login API
    
    Handles user authentication via Google OAuth tokens.
    Creates or retrieves user accounts and returns JWT tokens.
    """
    
    @swagger_auto_schema(
        operation_description="Login user with Google OAuth token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['token'],
            properties={
                'token': openapi.Schema(type=openapi.TYPE_STRING, description='Google OAuth token'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Google login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER, description='HTTP status code'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
                        'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                        'reg_user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Register user ID'),
                        'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                        'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
                        'phone': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number'),
                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='Full name'),
                        'profile_image': openapi.Schema(type=openapi.TYPE_STRING, description='Profile image URL'),
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid Google token",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
                    }
                )
            )
        },
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        google_token = request.data.get('token')  # Token sent by the frontend

        # Verify the Google token
        try:
            google_data = verify_google_token(google_token)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Remove the domain from the email to create the username
        username = google_data['email'].split('@')[0]

        # Check if the user exists by email, and create the user if not
        user, created = User.objects.get_or_create(
            email=google_data['email'],
            defaults={'username': username, 'first_name': google_data['given_name'], 'last_name': google_data['family_name']}
        )

        # Create or update the Register model
        register, created = Register.objects.get_or_create(user=user)
        
        # download profile picture
        if google_data.get('picture'):
            try:
                response = requests.get(google_data['picture'])
                if response.status_code == 200 and created:
                    file_name = f"{username}_profile.jpg"
                    register.profile_image.save(file_name, ContentFile(response.content), save=True)
            except Exception as e:
                print("Error downloading profile image:", e)
        

        # if created:
        #     register.profile_image = google_data.get('picture')  # Save the profile image URL
        #     register.save()

        # Generate access and refresh tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "status": status.HTTP_200_OK,
            'refresh': str(refresh),
            'access': access_token,
            'user_id': user.id,
            'reg_user_id': register.id,
            'username': user.username,
            'email': user.email,
            'phone': register.phonenumber,
            'name': f'{user.first_name} {user.last_name}',
            'profile_image': register.profile_image_url,
        })

class ReferralHistoryView(APIView):
    """
    Referral History API
    
    Retrieves referral history for authenticated users.
    Shows users who were referred by the current user.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get referral history for the authenticated user",
        responses={
            200: openapi.Response(
                description="Referral history retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'referral_history': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'referral_code': openapi.Schema(type=openapi.TYPE_STRING, description='Referral code'),
                                    'inviter': openapi.Schema(type=openapi.TYPE_STRING, description='Inviter username'),
                                    'invitee': openapi.Schema(type=openapi.TYPE_STRING, description='Invitee username'),
                                    'date_referred': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Date of referral'),
                                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='Referral status'),
                                }
                            )
                        ),
                        'referrel_code': openapi.Schema(type=openapi.TYPE_STRING, description='User\'s referral code'),
                    }
                )
            )
        },
        tags=['Referrals']
    )
    def get(self, request, *args, **kwargs):
        user = Register.objects.filter(user=request.user).first()
        referrals = Referral.objects.filter(inviter=user)
        serializer = ReferralHistorySerializer(referrals, many=True)
        return Response({"referral_history": serializer.data, "referrel_code": user.referral_code}, status=status.HTTP_200_OK)
