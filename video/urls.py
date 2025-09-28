
from django.urls import path
from .views import (

    LikeAPIView, LikeDetailView,
    CommentCreateAPIView, CommentDetailView,
    FavoriteListCreateView, FavoriteDetailView,
    ShareListCreateView, ShareDetailView,
    MergeVideoAndMusic, RemoveTempVideo,
    PostShuffledListAPIView, LikeListView,ParticipantListCreateView, ParticipantDetailView, UserVideosAPIView, ParticipantTempSave
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
]

