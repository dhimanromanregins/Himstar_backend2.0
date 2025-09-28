from django.urls import path
from .views import ContactCreateView,UserContactsView

urlpatterns = [
    path('contact/', ContactCreateView.as_view(), name='contact-create'),
    path('user_contacts/', UserContactsView.as_view(), name='user-contacts'),
]
