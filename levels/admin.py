from django.contrib import admin
from .models import Stage, Level, Stage_Levels
# Register your models here.
admin.site.register(Stage)
admin.site.register(Stage_Levels)
admin.site.register(Level)