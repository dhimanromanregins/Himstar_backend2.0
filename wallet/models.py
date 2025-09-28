from django.db import models
from accounts.models import Register, Referral

class BankDetail(models.Model):
    user = models.OneToOneField(Register, on_delete=models.CASCADE, related_name="bank_detail")
    account_holder_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=20, unique=True)
    ifsc_code = models.CharField(max_length=11)
    branch_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.account_holder_name} - {self.bank_name}"
    

class WithdrawalRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSED', 'Processed'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.ForeignKey(Register, on_delete=models.CASCADE, related_name="withdrawal_requests")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"User: {self.user.user.username}, Amount: {self.amount}, Status: {self.status}"

class ReferrelPaymentHistory(models.Model):
    amount = models.IntegerField(default=0)
    referrel = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='referrel_payment')
    processed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.referrel.referral_code} - Rs.{self.amount}'
