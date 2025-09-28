from django.db import models
from dashboard.models import Category
from django.conf import settings
# from utils.helpers import delete_blob_from_azure, AzureMediaStorage


class BannerOrVideo(models.Model):
    BANNER = 'banner'
    VIDEO = 'video'

    MEDIA_TYPE_CHOICES = [
        (BANNER, 'Banner'),
        (VIDEO, 'Video'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPE_CHOICES,
        default=BANNER
    )

    banner_image = models.ImageField(upload_to='banners/', blank=True, null=True)
    # banner_image = models.ImageField(storage=AzureMediaStorage(), upload_to='banners/', blank=True, null=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    # video_file = models.FileField(storage=AzureMediaStorage(), upload_to='videos/', blank=True, null=True)
    file_uri = models.CharField(max_length=1000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    # def delete(self, *args, **kwargs):
    #     """Delete the file from Azure Blob Storage before deleting the model instance"""
    #     print('*************')
    #     if self.banner_image:
    #         delete_blob_from_azure(self.file_uri)
    #     if self.video_file:
    #         delete_blob_from_azure(self.file_uri)
    #     super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        # Ensure only one of banner_image or video_file is uploaded
        # if self.media_type == self.BANNER:
        #     self.video_file = None
        # elif self.media_type == self.VIDEO:
        #     self.banner_image = None
        # print('*args, **kwargs>>>>>', *args, '||||', **kwargs)
        super().save(*args, **kwargs)  # Save the instance first

        # Generate and save the file URL
        if self.media_type == self.BANNER and self.banner_image:
            # self.file_uri = f"{settings.AZURE_FRONT_DOOR_DOMAIN}/{self.banner_image.name}"
            self.file_uri = f"{settings.DOMAIN_URL}{self.banner_image.url}"
        elif self.media_type == self.VIDEO and self.video_file:
            # self.file_uri = f"{settings.AZURE_FRONT_DOOR_DOMAIN}/{self.video_file.name}"
            self.file_uri = f"{settings.DOMAIN_URL}{self.video_file.url}"

        super().save(update_fields=['file_uri'])  # Save the updated URL
