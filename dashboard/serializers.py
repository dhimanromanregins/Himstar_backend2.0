# serializers.py
from django.utils.timezone import localtime
from django.utils.timezone import now
from rest_framework import serializers
from .models import Category, Round, Tournament, CompetitionMedia
from video.models import Participant
from payments.models import PaymentDetails
from accounts.models import Register
from video.models import Like
from django.utils import timezone

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


# serializers.py
from rest_framework import serializers
from .models import Competition, PrizeBreakdown
from video.models import Participant

class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_id = self.context.get('user_id')
        register = Register.objects.filter(user=user_id).first()
        is_participated = Participant.objects.filter(competition=instance, user=register).first()
        participants = Participant.objects.filter(competition=instance)
        videos_id = Participant.objects.filter(user=user_id).values_list('id', flat=True)
        likes = Like.objects.filter(post__id__in=videos_id).count()
        representation['total_likes'] = likes

        # This is for registration_close_date
        representation['reg_close_date'] = localtime(instance.registration_close_date).strftime(
            "%B %d, %Y at %I:%M %p") if instance.registration_close_date else None

        # This is for registration_open_date
        representation['reg_open_date'] = localtime(instance.registration_open_date).strftime(
            "%B %d, %Y at %I:%M %p") if instance.registration_open_date else None

        # This is for start date
        representation['start_date_formatted'] = localtime(instance.start_date).strftime(
            "%B %d, %Y at %I:%M %p") if instance.start_date else None

        # This is for End date
        representation['end_date_formatted'] = localtime(instance.end_date).strftime(
            "%B %d, %Y at %I:%M %p") if instance.end_date else None

        # Check if stage exists and has likes_required attribute
        if instance.stage and hasattr(instance.stage, 'likes_required'):
            if instance.stage.likes_required <= likes:
                representation['can_participate'] = True
            else:
                representation['can_participate'] = False
        else:
            # If likes_required is not set, allow participation
            representation['can_participate'] = True
        representation['category'] = instance.category.name if instance.category else None
        representation['rules'] = instance.rules.split('\n') if instance.rules else instance.rules
        representation['is_participated'] = True if is_participated else False
        if is_participated and is_participated.temp_video:
            representation['temp_video'] = is_participated.file_uri
        representation['stage'] = instance.stage.name.name if instance.stage else None
        if instance.competition_type == 'competition':
            representation['is_close'] = instance.end_date < now()
        representation['is_done'] = True if is_participated and (is_participated.file_uri and is_participated.is_paid) else False
        if instance.competition_type == 'competition':
            representation['reg_open'] = instance.registration_open_date <= now() and instance.registration_close_date >= now()
            representation['reg_close'] = instance.registration_close_date < now()
        else:
            representation['reg_open'] = None
            representation['reg_close'] = None
        representation['remaining_slots'] = instance.max_participants - participants.filter(is_paid=True).count() if instance.max_participants else 0
        representation['registration_open_date'] = localtime(instance.registration_open_date).strftime(
            "%Y-%m-%d %H:%M:%S") if instance.registration_open_date else None
        representation['registration_close_date'] = localtime(instance.registration_close_date).strftime(
            "%Y-%m-%d %H:%M:%S") if instance.registration_close_date else None
        representation['start_date'] = localtime(instance.start_date).strftime(
            "%Y-%m-%d %H:%M:%S") if instance.start_date else None
        representation['end_date'] = localtime(instance.end_date).strftime(
            "%Y-%m-%d %H:%M:%S") if instance.end_date else None
        representation['max_participants'] = instance.max_participants
        
        # Check if user has paid for this competition
        representation['user_has_paid'] = bool(is_participated and is_participated.is_paid) if is_participated else False
        
        # Check if competition requires payment
        representation['is_paid_competition'] = bool(instance.price and instance.price > 0)

        media_files = CompetitionMedia.objects.filter(competition=instance)
        files = []
        for file in media_files:
            data = {}
            data['title'] = file.title
            if file.media_type == CompetitionMedia.VIDEO:
                data['url'] = file.video_file.url
            elif file.media_type == CompetitionMedia.SOUND:
                data['url'] = file.video_file.url
            else:
                data['url'] = file.music_file.url
            files.append(data)

        representation['media_files'] = files

        return representation

class RoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Round
        fields = '__all__'



class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tournament
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_id = self.context.get('user_id')
        past_tournaments = self.context.get('past_tournaments')
        register = Register.objects.filter(user=user_id).first()
        # current_competition = instance.competitions.filter(is_active=True).first()
        current_time = timezone.localtime(timezone.now())
        if instance.end_date < now():
            current_competition = instance.competitions.last()
            print(current_competition)
        else:
            current_competition = instance.competitions.filter(
                is_active=True,
                end_date__gte=now()
            ).first()
        is_participated = Participant.objects.filter(competition=current_competition, user=register).first()
        participants = Participant.objects.filter(competition=current_competition) if current_competition else Participant.objects.none()
        
        # Initialize serializer only if current_competition exists
        if current_competition:
            current_competition_serailzer = CompetitionSerializer(current_competition)
            current_competition_data = current_competition_serailzer.data
        else:
            current_competition_data = {}
            
        payment = PaymentDetails.objects.filter(user=register, tournament=instance).first()
        representation['category'] = instance.category.name
        representation['tour_id'] = instance.id

        representation['reg_close_date'] = localtime(instance.registration_close_date).strftime("%B %d, %Y at %I:%M %p") if instance.registration_close_date else None

        representation['reg_open_date'] = localtime(instance.registration_open_date).strftime("%B %d, %Y at %I:%M %p") if instance.registration_open_date else None

        representation['start_date_formatted'] = localtime(instance.start_date).strftime("%B %d, %Y at %I:%M %p") if instance.start_date else None

        representation['end_date_formatted'] = localtime(instance.end_date).strftime("%B %d, %Y at %I:%M %p") if instance.end_date else None

        # representation['stage'] = instance.stage.name.name
        representation['competition_type'] = 'tournament'
        # representation['is_participated'] = True if is_participated else False
        representation['is_participated'] = True if is_participated else False
        if is_participated and is_participated.temp_video:
            representation['temp_video'] = is_participated.temp_video.url
        representation['is_close'] = instance.end_date < now()
        representation['is_done'] = True if is_participated and ((is_participated.file_uri or (is_participated.video and 'media' in is_participated.video.url)) and is_participated.is_paid) else False
        
        # Check if current_competition exists before accessing its attributes
        if current_competition:
            representation['reg_open'] = current_competition.registration_open_date <= current_time and current_competition.registration_close_date >= current_time
            representation['reg_close'] = current_competition.registration_close_date < now()
        else:
            representation['reg_open'] = False
            representation['reg_close'] = True
        representation['remaining_slots'] = (instance.max_participants - participants.filter(is_paid=True).count()) if instance.max_participants and current_competition else 0
        representation['is_paid'] = True if payment else False
        
        # Check if user has paid for this tournament (same logic as competition)
        representation['user_has_paid'] = bool(is_participated and is_participated.is_paid) if is_participated else False
        
        representation['competition'] = current_competition_data
        representation['rules'] = instance.rules.split('\n') if instance.rules else instance.rules
        
        # Get media files only if current_competition_data has an id
        competition_id = current_competition_data.get('id') if current_competition_data else None
        media_files = CompetitionMedia.objects.filter(competition=competition_id) if competition_id else CompetitionMedia.objects.none()
        representation['registration_open_date'] = localtime(instance.registration_open_date).strftime(
            "%Y-%m-%d %H:%M:%S") if instance.registration_open_date else None
        representation['registration_close_date'] = localtime(instance.registration_close_date).strftime(
            "%Y-%m-%d %H:%M:%S") if instance.registration_close_date else None
        representation['start_date'] = localtime(instance.start_date).strftime(
            "%Y-%m-%d %H:%M:%S") if instance.start_date else None
        representation['end_date'] = localtime(instance.end_date).strftime(
            "%Y-%m-%d %H:%M:%S") if instance.end_date else None

        files = []
        for file in media_files:
            data = {
                'title': file.title,
                'url': None
            }
            # Handle file URLs based on media type
            if file.media_type == CompetitionMedia.VIDEO:
                data['url'] = file.video_file.url if file.video_file else None
            elif file.media_type == CompetitionMedia.SOUND:
                data['url'] = file.sound_file.url if file.sound_file else None
            else:  # Default to music files
                data['url'] = file.music_file.url if file.music_file else None

            if data['url']:  # Add only if the URL exists
                files.append(data)

        representation['media_files'] = files
        return representation


# class MyCompetitionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Participant
#         fields = '__all__'

    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     user_id = self.context.get('user_id')
    #     is_participated = Participant.objects.filter(competition=instance, user=user_id).first()
    #     representation['category'] = instance.category.name
    #     representation['is_participated'] = True if is_participated else False
    #     representation['is_done'] = True if is_participated.file_uri else False
    #     representation['is_live'] = instance.start_date <= now()
    #     return representation

class PrizeBreakdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrizeBreakdown
        fields = '__all__'