from rest_framework import serializers
from .models import Stage, Level

class StageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stage
        fields = '__all__'

class LevelSerializer(serializers.ModelSerializer):
    current_stage_name = serializers.ReadOnlyField(source='current_stage.name')

    class Meta:
        model = Level
        fields = '__all__'
