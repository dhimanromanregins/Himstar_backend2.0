# serializers.py
from rest_framework import serializers
from .models import Participant, Like, Comment, Favorite, Share
from accounts.models import Register


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = '__all__'
    
    def to_representation(self, instance):
        likes = Like.objects.filter(post=instance.id).count()
        comments = Comment.objects.filter(post=instance.id).count()

        user_id = self.context.get('user_id')
        register = Register.objects.filter(user=user_id).first()
        print(register)
        is_like = Like.objects.filter(post=instance.id, user=register).first()

        representation = super().to_representation(instance)
        representation['username'] = instance.user.user.username
        representation['profile_image'] = instance.user.profile_image_url
        representation['is_like'] = True if is_like else False
        representation['likes'] = likes
        representation['comments'] = comments
        representation['video'] = instance.video.url if instance.video else instance.file_uri
        representation['comp_id'] = instance.competition.unique_id
        return representation


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'created_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['username'] = instance.user.user.username
        representation['profile_image'] = instance.user.profile_image_url
        return representation


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'user', 'post', 'content', 'created_at']
        read_only_fields = ['created_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['username'] = instance.user.user.username
        representation['profile_image'] = instance.user.profile_image_url
        return representation


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'user', 'post', 'created_at']


class ShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Share
        fields = ['id', 'user', 'post', 'share_url', 'created_at']
