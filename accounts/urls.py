from django.urls import path
from .views import RegisterView, VerifyOTPAndRegisterView, LoginView, AwardsAPIView,RegisterDetailAPIView,GoogleLoginView, ReferralHistoryView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPAndRegisterView.as_view(), name='verify-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('awards/', AwardsAPIView.as_view(), name='awards_api'),
    path('profile/', RegisterDetailAPIView.as_view(), name='register_detail'),
    path('google-register/', GoogleLoginView.as_view(), name='google-login'),
    path('referral-history/', ReferralHistoryView.as_view(), name='referral-history'),
]
