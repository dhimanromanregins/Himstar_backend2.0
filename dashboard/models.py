from django.db import models
from accounts.models import Register
from django.utils import timezone
from datetime import datetime, timedelta
from ckeditor.fields import RichTextField
# import boto3
from django.conf import settings
from botocore.exceptions import NoCredentialsError
import os
from levels.models import Stage
import uuid
from django.core.exceptions import ValidationError
# from utils.helpers import AzureMediaStorage, delete_blob_from_azure




class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    # Assuming you already have a Category model for categorizing competitions
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Competition(models.Model):
    TOURNAMENT = 'tournament'
    COMPETITION = 'competition'

    COMPETITION_TYPE_CHOICES = [
        (TOURNAMENT, 'Tournament'),
        (COMPETITION, 'Competition'),
    ]
    # tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, null=True, blank=True)
    stage = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    registration_open_date = models.DateTimeField(blank=True, null=True)
    registration_close_date = models.DateTimeField(blank=True, null=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True)
    competition_type = models.CharField(
        max_length=100,
        choices=COMPETITION_TYPE_CHOICES,
        default=COMPETITION
    )
    price = models.BigIntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    # is_online = models.BooleanField(default=False)
    banner_image = models.ImageField(upload_to='competition_banners/', blank=True, null=True)
    file_uri = models.CharField(max_length=255, blank=True, null=True)
    rules = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    winning_price = models.CharField(max_length=255, null=True, blank=True)
    unique_id = models.CharField(unique=True, editable=False, max_length=12)

    # parent_tournament = models.ForeignKey(
    #     'self',
    #     on_delete=models.CASCADE,
    #     related_name='sub_competitions',
    #     blank=True,
    #     null=True,
    #     help_text="Specify the tournament if this is a round/competition within a tournament."
    # )

    def __str__(self):
        return self.name

    # def delete(self, *args, **kwargs):
    #     """Delete the file from Azure Blob Storage before deleting the model instance"""
    #     if self.banner_image:
    #         delete_blob_from_azure(self.file_uri)
    #     super().delete(*args, **kwargs)
    
    def save(self, *args, **kwargs):
        if not self.unique_id:
            unique_id = f"COMP{uuid.uuid4().hex[:8].upper()}"
            while Competition.objects.filter(unique_id=unique_id).exists():
                unique_id = f"COMP{uuid.uuid4().hex[:8].upper()}"
            self.unique_id = unique_id

        super().save(*args, **kwargs)  # Save the instance first

        # Store the Azure Blob URL in `file_uri`
        if self.banner_image:
            self.file_uri = f"{settings.DOMAIN_URL}{self.banner_image.url}"
            super().save(update_fields=['file_uri'])

    @property
    def is_tournament(self):
        return self.competition_type == self.TOURNAMENT

    @property
    def has_sub_competitions(self):
        return self.sub_competitions.exists()

    # def __str__(self):
    #     return self.user

class Tournament(models.Model):
    name = models.CharField(max_length=255)
    total_rounds = models.PositiveIntegerField(null=True, blank=True)
    competitions = models.ManyToManyField(Competition, related_name='tournaments')
    description = models.TextField(null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_open_date = models.DateTimeField(null=True, blank=True)
    registration_close_date = models.DateTimeField(null=True, blank=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    stage = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True, blank=True)
    banner_image = models.ImageField(upload_to='tournament_banners/', blank=True, null=True)
    file_uri = models.CharField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    rules = models.TextField(blank=True, null=True)
    price = models.BigIntegerField()
    is_active = models.BooleanField(default=True)
    winning_price = models.CharField(max_length=255, null=True, blank=True)
    unique_id = models.CharField(unique=True, editable=False, max_length=12)
    # is_online = models.BooleanField(default=False)
    def __str__(self):
        return f"Tournament: {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.unique_id:
            unique_id = f"TOUR{uuid.uuid4().hex[:8].upper()}"
            while Tournament.objects.filter(unique_id=unique_id).exists():
                unique_id = f"TOUR{uuid.uuid4().hex[:8].upper()}"
            self.unique_id = unique_id
        super().save(*args, **kwargs)
        if self.banner_image:
            self.file_uri = f"{settings.DOMAIN_URL}{self.banner_image.url}"
            super().save(update_fields=['file_uri'])

    # def delete(self, *args, **kwargs):
    #     """Delete the file from Azure Blob Storage before deleting the model instance"""
    #     if self.banner_image:
    #         delete_blob_from_azure(self.file_uri)
    #     super().delete(*args, **kwargs)





class Round(models.Model):
    competition = models.ForeignKey(Competition, related_name="rounds", on_delete=models.CASCADE)
    round_number = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    eliminated_percentage = models.PositiveIntegerField(default=20)  # Percentage eliminated after each round
    max_participants = models.PositiveIntegerField()  # Maximum participants for this round

    def __str__(self):
        return f"Round {self.round_number} of {self.competition.name}"

    def eliminate_participants(self):
        # Eliminate a percentage of participants for the current round based on 'eliminated_percentage'
        total_participants = self.competition.participants.count()
        num_to_eliminate = (total_participants * self.eliminated_percentage) // 100
        participants_to_eliminate = self.competition.participants.all()[:num_to_eliminate]  # Just an example elimination strategy
        for participant in participants_to_eliminate:
            participant.is_qualified_for_next_round = False
            participant.save()




class CompetitionMedia(models.Model):
    VIDEO = 'video'
    SOUND = 'sound'
    MUSIC = 'music'

    MEDIA_TYPE_CHOICES = [
        (VIDEO, 'Video'),
        (SOUND, 'Sound'),
        (MUSIC, 'Music'),
    ]
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='media')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    video_file = models.FileField(upload_to='competition_videos/', blank=True, null=True)
    sound_file = models.FileField(upload_to='competition_sounds/', blank=True, null=True)
    music_file = models.FileField(upload_to='competition_music/', blank=True, null=True)
    title = models.CharField(max_length=250)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.competition.name} - {self.get_media_type_display()}"

    def save(self, *args, **kwargs):
        if self.media_type == self.VIDEO:
            self.sound_file = None
            self.music_file = None
        elif self.media_type == self.SOUND:
            self.video_file = None
            self.music_file = None
        elif self.media_type == self.MUSIC:
            self.video_file = None
            self.sound_file = None
        super().save(*args, **kwargs)


class Winnings(models.Model):
    user = models.ForeignKey(Register, on_delete=models.CASCADE)
    Competition = models.ForeignKey


class PrizeBreakdown(models.Model):
    TOURNAMENT = 'Tournament'
    COMPETITION = 'Competition'

    TYPE_CHOICES = [
        (TOURNAMENT, 'tournament'),
        (COMPETITION, 'competition'),
    ]

    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=COMPETITION
    )
    competition = models.ForeignKey(
        'Competition',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    tournament = models.ForeignKey(
        'Tournament',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    position = models.CharField(max_length=255)
    prize = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.type == self.COMPETITION and not self.competition:
            raise ValidationError({'competition': 'Competition is required when type is Competition.'})
        if self.type == self.TOURNAMENT and not self.tournament:
            raise ValidationError({'tournament': 'Tournament is required when type is Tournament.'})

    def __str__(self):
        return f"{self.position} - {self.prize} ({self.type})"

