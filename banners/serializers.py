from rest_framework import serializers
from .models import BannerOrVideo

class BannerOrVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BannerOrVideo
        fields = ['title', 'description', 'file_uri', 'banner_image', 'media_type', 'video_file']
