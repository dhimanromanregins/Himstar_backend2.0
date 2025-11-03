from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
# from utils.helpers import AzureMediaStorage, delete_blob_from_azure
from django.conf import settings
import datetime
import uuid


class Register(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    custom_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    phonenumber = models.CharField(max_length=15, validators=[RegexValidator(r'^\d{10,15}$')], null=True, blank=True)
    zipcode = models.CharField(max_length=10, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    points = models.BigIntegerField(default=0)
    votes = models.BigIntegerField(default=0)
    cover_image = models.ImageField(upload_to='cover-images/', blank=True, null=True)
    cover_image_url = models.CharField(max_length=1000, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile-images/', blank=True, null=True)
    profile_image_url = models.CharField(max_length=1000, blank=True, null=True)
    referral_code = models.CharField(max_length=100, unique=True, null=True)

    def save(self, *args, **kwargs):
        # Ensure unique custom_id and referral_code
        if not self.custom_id:
            unique_id = f"CUS{uuid.uuid4().hex[:8].upper()}"
            while Register.objects.filter(custom_id=unique_id).exists():
                unique_id = f"CUS{uuid.uuid4().hex[:8].upper()}"
            self.custom_id = unique_id

        if not self.referral_code:
            referral_code = f"REF{uuid.uuid4().hex[:8].upper()}"
            while Register.objects.filter(referral_code=referral_code).exists():
                referral_code = f"REF{uuid.uuid4().hex[:8].upper()}"
            self.referral_code = referral_code

        super().save(*args, **kwargs)  # First save the instance to generate the file name

        # Update cover_image_url and profile_image_url after saving
        update_fields = []
        if self.cover_image:
            self.cover_image_url = self.cover_image.url
            update_fields.append("cover_image_url")

        if self.profile_image:
            self.profile_image_url = self.profile_image.url
            update_fields.append("profile_image_url")

        if update_fields:
            super().save(update_fields=update_fields)



    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"


class Referral(models.Model):
    inviter = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='referrals_made')
    invitee = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='referred_by')
    referral_code = models.CharField(max_length=100)
    date_referred = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('confirmed', 'Confirmed')],
                              default='pending')

    def __str__(self):
        return f"Referral: {self.inviter} -> {self.invitee} ({self.status})"

class ReferralReward(models.Model):
    amount = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Referral Reward: Rs.{self.amount}"

class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return False  # OTP never expires
    

class Awards(models.Model):
    name = models.CharField(max_length=255)
    # image = models.ImageField(storage=AzureMediaStorage(), upload_to="awards")
    image = models.ImageField(upload_to="awards")
    votes_required = models.CharField(max_length=255)
    image_uri = models.CharField(max_length=1000, blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.image:
            # self.image_uri = f"{settings.AZURE_FRONT_DOOR_DOMAIN.rstrip('/')}/{self.image.name.lstrip('/')}"
            self.image_uri = f"{settings.DOMAIN_URL}{self.image.url}"
        
        super().save(update_fields=['image_uri'])

    # def delete(self, *args, **kwargs):
    #     """Delete the video from Azure Blob Storage before deleting the model instance"""
    #     if self.image:
    #         delete_blob_from_azure(self.image_uri)  # Call the function to delete the blob
    #     super().delete(*args, **kwargs)
    
    def __str__(self):
        return self.name


