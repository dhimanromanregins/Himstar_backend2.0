from django.contrib import admin
from .models import BankDetail, WithdrawalRequest, ReferrelPaymentHistory

admin.site.register(BankDetail)
admin.site.register(WithdrawalRequest)
admin.site.register(ReferrelPaymentHistory)
