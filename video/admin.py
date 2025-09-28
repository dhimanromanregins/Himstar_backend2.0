from django.contrib import admin
from .models import  Favorite, Like, Comment, Share, Participant
# Register your models here.

admin.site.register(Favorite)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Share)
@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    readonly_fields = ('file_uri',)
