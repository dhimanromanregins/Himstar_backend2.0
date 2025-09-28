from django.urls import path
from .views import BankDetailRetrieveUpdateDestroyAPIView, WithdrawalRequestAPIView, WalletHistory

urlpatterns = [
    path('bankdetails/', BankDetailRetrieveUpdateDestroyAPIView.as_view(), name='bankdetail-retrieve-update-destroy'),
    path('withdrawal/', WithdrawalRequestAPIView.as_view(), name='withdrawal-api'),
    path('wallet-history/', WalletHistory.as_view(), name='wallet-history'),
]
