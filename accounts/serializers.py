from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Register, OTP, Awards, Referral
from .utils import generate_otp, send_otp
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from video.serializers import ParticipantSerializer
from video.models import Participant, Like


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True) 
    phonenumber = serializers.CharField(required=True)
    zipcode = serializers.CharField(required=True)
    gender = serializers.ChoiceField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], required=True)
    dob = serializers.DateField(required=True)
    password = serializers.CharField(source="user.password", write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    eligible_awards = serializers.SerializerMethodField()
    participations = ParticipantSerializer(many=True, source='participant_set', read_only=True)
    is_password = serializers.SerializerMethodField()

    class Meta:
        model = Register
        fields = [
            'custom_id', 'username', 'email', 'phonenumber', 'zipcode', 'gender', 'dob',
            'points', 'votes', 'cover_image', 'profile_image', 'eligible_awards', 'confirm_password','password','first_name', 'last_name', 'participations','is_password'
        ]

    def get_is_password(self, obj):
        # Check if the user has a password set
        user = obj.user
        return bool(user.password and user.password != "")


    def validate(self, data):
        print('data>>>>', data)
        # Check if username already exists
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "Username already exists"})

        # Check if email already exists
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists"})

        # Check if phone number already exists
        if Register.objects.filter(phonenumber=data['phonenumber']).exists():
            raise serializers.ValidationError({"phonenumber": "Phone number already exists"})

        # Check if passwords match
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return data

    def create(self, validated_data):
        email = validated_data['email']

        # Generate OTP and store it in the OTP model
        otp_code = generate_otp()
        OTP.objects.update_or_create(email=email, defaults={'otp': otp_code})

        # Send OTP to the user's email
        send_otp(email, otp_code)

        return validated_data
    
    def get_eligible_awards(self, obj):
        eligible_awards = Awards.objects.filter(votes_required__gte=50)
        return AwardsSerializer(eligible_awards, many=True).data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_id = self.context.get('user_id')
        videos_id = Participant.objects.filter(user=user_id).values_list('id', flat=True)
        likes = Like.objects.filter(post__id__in=videos_id).count()
        representation['total_likes'] = likes
        representation['profile_image'] = instance.profile_image_url
        representation['cover_image'] = instance.cover_image_url
        print('representation>>>', representation)
        # awards = Awards.objects.all()
        # my_awards = []
        # for award in awards:
        #     if int(award.votes_required) <= 50:
        #         my_awards.append(award.image_uri)
        # representation['awards'] = my_awards
        return representation
    


class RegisterSerializerPasswordUpdate(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True) 
    phonenumber = serializers.CharField(required=True)
    zipcode = serializers.CharField(required=True)
    gender = serializers.ChoiceField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], required=True)
    dob = serializers.DateField(required=True)
    password = serializers.CharField( write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = Register
        fields = [
            'custom_id', 'username', 'email', 'phonenumber', 'zipcode', 'gender', 'dob',
            'points', 'votes', 'cover_image', 'profile_image',  'confirm_password','password','first_name', 'last_name',
        ]


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def create(self, validated_data):
        email = validated_data['email']
        otp = generate_otp()

        # Create or update OTP
        OTP.objects.update_or_create(email=email, defaults={'otp': otp})

        # Send the OTP to the user's email
        send_otp(email, otp)

        return validated_data


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data['email']
        otp = data['otp']
        print('data>>>>', data)

        # Check if the OTP is valid
        try:
            otp_record = OTP.objects.get(email=email, otp=otp)
            print('otp_record>>>>', otp_record)
            if otp_record.is_expired():
                raise serializers.ValidationError("OTP has expired.")
        except OTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP.")

        return data

    def create(self, validated_data):
        email = validated_data['email']

        # Fetch user data from the context (passed from the view)
        user_data = self.context['user_data']

        # Create the user
        # Handle full name splitting safely
        name_parts = user_data['fullName'].strip().split(' ')
        first_name = name_parts[0] if name_parts else ''
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        
        user = User.objects.create_user(
            username=user_data['username'],
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=user_data['password']
        )

        # Create Register
        register_user = Register.objects.create(
            user=user,
            phonenumber=user_data['phonenumber'],
            zipcode=user_data['zipcode'],
            gender=user_data['gender'],
            dob=user_data['dob']
        )

        ref_code = user_data.get('ref_code')
        if ref_code:
            inviter = Register.objects.filter(referral_code=ref_code).first()
            if inviter:
                Referral.objects.create(inviter=inviter, invitee=register_user, referral_code=ref_code)

        # OTP verified and user registered
        return user

class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username_or_email = data.get("username_or_email")
        password = data.get("password")

        user = authenticate(username=username_or_email, password=password)
        if not user:
            # Try by email if no user with that username exists
            user_model = User.objects.filter(email=username_or_email).first()
            if user_model:
                user = authenticate(username=user_model.username, password=password)

        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials")

    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }
    

class AwardsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Awards
        fields = ['name', 'image', 'votes_required', 'image_uri']

class ReferralHistorySerializer(serializers.ModelSerializer):
    inviter = serializers.StringRelatedField()  # Assuming 'inviter' is a User instance
    invitee = serializers.StringRelatedField()  # Assuming 'invitee' is a User instance

    class Meta:
        model = Referral
        fields = ['referral_code', 'inviter', 'invitee', 'date_referred', 'status']