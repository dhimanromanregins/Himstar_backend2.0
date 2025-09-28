from rest_framework import serializers
from .models import PaymentDetails

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentDetails
        fields = '__all__'
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        banner = None
        if instance.competition:
            banner = instance.competition.file_uri

        representation['banner'] = banner
        return representation