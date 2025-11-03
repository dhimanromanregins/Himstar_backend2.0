from django.db import models
from django.contrib.auth import get_user_model
from dashboard.models import Competition, Tournament
from accounts.models import Register
import uuid
from django.conf import settings
# from storages.backends.azure_storage import AzureStorage
# from utils.helpers import delete_blob_from_azure, AzureMediaStorage

import os
User = get_user_model()

def generate_video_filename(instance, filename):
    extension = filename.split('.')[-1]
    return f"videos/{uuid.uuid4()}.{extension}"

class Participant(models.Model):
    competition = models.ForeignKey(
        Competition, related_name="participants", on_delete=models.SET_NULL, null=True, blank=True
    )
    user = models.ForeignKey(Register, on_delete=models.CASCADE)

    # Store videos in Azure Blob Storage
    video = models.FileField(upload_to='competition_participants_videos/', blank=True, null=True)

    # Store temp videos in local storage (MEDIA_ROOT)
    temp_video = models.FileField(upload_to='competition_participants_videos/', blank=True, null=True)

    file_uri = models.CharField(max_length=500, blank=True, null=True)
    is_paid = models.BooleanField(default=False)


    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)  # Save the instance first

    #     # Generate and store the Azure Blob URL for the main video
    #     if self.video:
    #         self.file_uri = f"{settings.AZURE_FRONT_DOOR_DOMAIN}/{self.video.name}"
    #         super().save(update_fields=['file_uri'])

    # def delete(self, *args, **kwargs):
    #     """Delete the file from Azure Blob Storage before deleting the model instance"""
    #     print('&&&&&&&&&&&&&&&&&')
    #     if self.video:
    #         delete_blob_from_azure(self.file_uri)
    #     if self.temp_video:
    #         delete_blob_from_azure(self.file_uri)
    #     super().delete(*args, **kwargs)

    # def cleanup_video_files(self):
    #     """
    #     Clean up video files associated with this participant
    #     """
    #     MEDIA_FOLDERS = [
    #         "competition_participants_temp_videos",
    #         "competition_participants_videos", 
    #         "merged_videos",
    #         "temp_videos"
    #     ]
        
    #     username = self.user.user.username
    #     print(f"Cleaning up video files for participant {self.id}, user: {username}")
        
    #     for folder in MEDIA_FOLDERS:
    #         folder_path = os.path.join("media", folder)
    #         if os.path.exists(folder_path):
    #             for file in os.listdir(folder_path):
    #                 if username in file:
    #                     file_path = os.path.join(folder_path, file)
    #                     try:
    #                         os.remove(file_path)
    #                         print(f"Deleted video file: {file_path}")
    #                     except Exception as e:
    #                         print(f"Error deleting file {file_path}: {e}")

    def __str__(self):
        return f"{self.user.user.username}"


class Like(models.Model):
    """Model to represent a like on a post."""
    user = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')  # A user can like a post only once.

    def __str__(self):
        return f"{self.user.user.username} likes {self.post}"


class Comment(models.Model):
    """Model to represent a comment on a post."""
    user = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.user.username} on {self.post}"


class Favorite(models.Model):
    """Model to represent a favorite post for a user."""
    user = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='favorites')
    post = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')  # A user can favorite a post only once.

    def __str__(self):
        return f"{self.user.user.username} favorited {self.post}"


class Share(models.Model):
    """Model to represent a shareable link for a post."""
    user = models.ForeignKey(Register, on_delete=models.CASCADE, related_name='shares')
    post = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='shares')
    share_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user.username} shared {self.post} with URL {self.share_url}"




