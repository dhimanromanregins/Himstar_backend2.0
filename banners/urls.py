from django.urls import path
from .views import BannersByCategoryAPIView

urlpatterns = [
    path('banners/', BannersByCategoryAPIView.as_view(), name='banners_api'),
    # path('banners/<int:category_id>/', BannersByCategoryAPIView.as_view(), name='banners_by_category_api'),
]
