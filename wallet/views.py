from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import  User
from .models import BankDetail, WithdrawalRequest, ReferrelPaymentHistory
from .serializers import BankDetailSerializer, WithdrawalRequestSerializer, ReferralPaymentHistorySerializer
from rest_framework.permissions import IsAuthenticated
from accounts.models import Register
from itertools import chain
from django.db.models import F
from datetime import datetime
import pytz


class BankDetailRetrieveUpdateDestroyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, id):
        try:
            return BankDetail.objects.get(user__user__id=id)
        except BankDetail.DoesNotExist:
            return None

    def get(self, request):
        bank_detail = self.get_object(request.user.id)
        print('bank_detail>>>', bank_detail)
        if bank_detail:
            serializer = BankDetailSerializer(bank_detail)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        register = Register.objects.filter(user=request.user).first()
        request.data['user'] = register.id
        serializer = BankDetailSerializer(data=request.data)
        print(request.data, '----------')
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        bank_detail = self.get_object(request.user.id)
        if bank_detail:
            bank_detail.delete()
            return Response(status=status.HTTP_200_OK)
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)


class WithdrawalRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        register_id = Register.objects.filter(user=request.user).first()
        withdrawals = WithdrawalRequest.objects.filter(user__user=request.user).order_by('-id')
        serializer = WithdrawalRequestSerializer(withdrawals, many=True)

        data =  {
            "withdrawal_history":serializer.data,
            "amount":  register_id.points
        }
        print(data, '-------------')
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        # Get the Register object for the authenticated user
        register = Register.objects.filter(user=request.user).first()

        if not register:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Add the user ID to the request data
        request.data['user'] = register.id  # Make sure this is correct

        # Get the amount from the withdrawal request
        amount = request.data.get('amount')

        if not amount:
            return Response({"detail": "Amount is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ensure that the amount is a positive value and cast it to a Decimal
            amount = float(amount)  # Convert amount to float

            # Check if the user has enough points
            if register.points < amount:
                return Response({"detail": "Insufficient points."}, status=status.HTTP_400_BAD_REQUEST)

            # Subtract the withdrawal amount from the user's points
            register.points -= amount
            register.save()

        except ValueError:
            return Response({"detail": "Invalid amount format."}, status=status.HTTP_400_BAD_REQUEST)

        # Serialize and save the withdrawal request
        serializer = WithdrawalRequestSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=register)  # Ensure 'user' is passed explicitly to the serializer
            register_id = Register.objects.filter(user=request.user).first()
            withdrawals = WithdrawalRequest.objects.filter(user__user=request.user).order_by('-id')
            serializer = WithdrawalRequestSerializer(withdrawals, many=True)
            data = {
                "withdrawal_history": serializer.data,
                "amount": register_id.points
            }
            return Response(data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WalletHistory(APIView):
    permission_classes = [IsAuthenticated]

    def format_datetime(self, datetime_value):
        if not datetime_value:
            return None
        if isinstance(datetime_value, str):
            dt_obj = datetime.strptime(datetime_value, "%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            dt_obj = datetime_value

        indian_timezone = pytz.timezone('Asia/Kolkata')
        dt_obj = dt_obj.astimezone(indian_timezone)

        return dt_obj.strftime("%I:%M%p %d %b %Y")

    def get(self, request):
        user = Register.objects.filter(user=request.user).first()
        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        withdrawals = WithdrawalRequest.objects.filter(user=user).annotate(
            date=F('requested_at')
        ).values(
            'amount', 'status', 'date'
        )

        referral_payments = ReferrelPaymentHistory.objects.filter(
            referrel__inviter=user
        ).annotate(
            date=F('processed_at')
        ).values(
            'amount', 'date', 'referrel__invitee__user__username'
        )

        referral_payments = [
            {
                **item,
                'invitee': item.pop('referrel__invitee__user__username'),
                'date': self.format_datetime(item['date'])
            }
            for item in referral_payments
        ]

        withdrawals = [
            {
                **item,
                'date': self.format_datetime(item['date'])
            }
            for item in withdrawals
        ]

        combined_data = sorted(
            chain(withdrawals, referral_payments),
            key=lambda x: x['date'],
            reverse=True
        )
        return Response({'wallet_history': combined_data, 'amount': user.points}, status=status.HTTP_200_OK)
