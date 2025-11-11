
from django.urls import path
from .views import (

    LikeAPIView, LikeDetailView,
    CommentCreateAPIView, CommentDetailView,
    FavoriteListCreateView, FavoriteDetailView,
    ShareListCreateView, ShareDetailView,
    MergeVideoAndMusic, RemoveTempVideo,
    PostShuffledListAPIView, LikeListView,ParticipantListCreateView, ParticipantDetailView, UserVideosAPIView, ParticipantTempSave,
    DeleteParticipantAPIView, CompetitionDetailForUserAPIView, ActiveCompetitionVideosAPIView, MediaDebugAPIView, RecoverParticipantVideosAPIView,
    ProductionMediaCheckAPIView, CompetitionTournamentVideosAPIView, GetVideosByIdAPIView, TimezoneInfoAPIView, TimeComparisonDebugAPIView
)

urlpatterns = [
    path('participants/<int:competition_pk>/', ParticipantListCreateView.as_view(), name='round-participants'),
    path('participant-update/', ParticipantDetailView.as_view(), name='participant-detail'),
    path('list-posts/', PostShuffledListAPIView.as_view(), name='post-list-view'),
     path('user-videos/', UserVideosAPIView.as_view(), name='user-videos'),
    # path('user-posts/<int:user>/', PostShuffledListAPIView2.as_view(), name='user-post-list-view'),

    path('like-post/', LikeAPIView.as_view(), name='like-create'),
    path('list-likes/<int:post_id>/', LikeListView.as_view(), name='like-list-view'),
    path('likes/<int:pk>/', LikeDetailView.as_view(), name='like-detail'),

    path('comment-post/', CommentCreateAPIView.as_view(), name='comment-create'),
    path('list-comments/<int:post_id>/', CommentDetailView.as_view(), name='comment-detail'),

    path('favorites/', FavoriteListCreateView.as_view(), name='favorite-list-create'),
    path('favorites/<int:pk>/', FavoriteDetailView.as_view(), name='favorite-detail'),

    path('shares/', ShareListCreateView.as_view(), name='share-list-create'),
    path('shares/<int:pk>/', ShareDetailView.as_view(), name='share-detail'),

    path('merge-video/', MergeVideoAndMusic.as_view(), name='merge_video_and_music'),
    path('remove-temp-video/', RemoveTempVideo.as_view(), name='remove_temp_video'),
    path('save-temp-participant/', ParticipantTempSave.as_view(), name='save-temp-participant'),
    path('delete-participant/', DeleteParticipantAPIView.as_view(), name='delete-participant'),
    path('competition-detail/<int:competition_id>/', CompetitionDetailForUserAPIView.as_view(), name='competition-detail-user'),
    path('active-competition-videos/', ActiveCompetitionVideosAPIView.as_view(), name='active-competition-videos'),
    path('competition-tournament-videos/', CompetitionTournamentVideosAPIView.as_view(), name='competition-tournament-videos'),
    path('videos/<int:entity_id>/', GetVideosByIdAPIView.as_view(), name='get-videos-by-id'),
    path('timezone-info/', TimezoneInfoAPIView.as_view(), name='timezone-info'),
    path('time-debug/', TimeComparisonDebugAPIView.as_view(), name='time-debug'),
    path('debug-media/', MediaDebugAPIView.as_view(), name='debug-media'),
    path('recover-videos/', RecoverParticipantVideosAPIView.as_view(), name='recover-videos'),
    path('check-production-media/', ProductionMediaCheckAPIView.as_view(), name='check-production-media'),
]

