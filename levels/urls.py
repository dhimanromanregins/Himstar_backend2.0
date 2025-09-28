from django.urls import path
from .views import StageAPIView, StageDetailAPIView, LevelAPIView

urlpatterns = [
    path('stages/', StageAPIView.as_view(), name='stage-list'),
    path('stages/<int:pk>/', StageDetailAPIView.as_view(), name='stage-detail'),
    path('levels/', LevelAPIView.as_view(), name='level-list'),
]
