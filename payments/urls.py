from django.urls import path
from .views import *

urlpatterns = [
    path('make-payment/', PaymentCreateGetAPIView.as_view(), name='make_payment'),
    path('payment-details/', PaymentCreateGetAPIView.as_view(), name='payment-view'),
    path('cleanup-unpaid/', CleanupUnpaidParticipantsAPIView.as_view(), name='cleanup_unpaid'),
    path('success/', successview, name='success'),
    path('failure/', failure, name='failure'),
]