from django.contrib import admin
from .models import Contact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone_number','status', 'message')
    search_fields = ('full_name', 'email', 'phone_number', 'message')
    list_filter = ('full_name', 'email', 'phone_number', 'status')
