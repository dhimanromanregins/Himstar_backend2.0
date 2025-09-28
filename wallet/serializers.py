from rest_framework import serializers
from .models import BankDetail,WithdrawalRequest, ReferrelPaymentHistory
from accounts.models import Register


class BankDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetail
        fields = '__all__'


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    requested_at_formatted = serializers.SerializerMethodField()
    processed_at_formatted = serializers.SerializerMethodField()

    class Meta:
        model = WithdrawalRequest
        fields = ['id', 'amount', 'status', 'requested_at', 'processed_at', 'requested_at_formatted',
                  'processed_at_formatted']

    def get_requested_at_formatted(self, obj):
        return obj.requested_at.strftime("%d/%m/%y %I:%M %p") if obj.requested_at else None

    def get_processed_at_formatted(self, obj):
        return obj.processed_at.strftime("%d/%m/%y %I:%M %p") if obj.processed_at else None

    def create(self, validated_data):
        validated_data['status'] = 'PENDING'
        return super().create(validated_data)


class ReferralPaymentHistorySerializer(serializers.ModelSerializer):
    referral_code = serializers.CharField(source='referrel.referral_code')
    inviter = serializers.StringRelatedField(source='referrel.inviter')

    class Meta:
        model = ReferrelPaymentHistory
        fields = ['referral_code', 'inviter', 'amount', 'processed_at']