from django.db import models
from accounts.models import Register
from dashboard.models import Tournament, Competition
# Create your models here.
from video.models import Participant


class Account(models.Model):
    user = models.OneToOneField(Register, on_delete=models.CASCADE, related_name="account")
    account_number = models.CharField(max_length=20, unique=True)
    bank_name = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=100, blank=True, null=True)
    ifsc_code = models.CharField(max_length=11)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.user.username}'s Account ({self.account_number})"



class PaymentDetails(models.Model):
    txnid = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mode = models.CharField(max_length=50)
    productinfo = models.CharField(max_length=255)
    firstname = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    status = models.CharField(max_length=50)
    cardCategory = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, null=True, blank=True)
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, null=True, blank=True)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Register, on_delete=models.CASCADE)

    def __str__(self):
        return f"Payment {self.txnid} - {self.status}"



# {'id': 403993715532817700, 'mode': 'CC', 'status': 'success', 'unmappedstatus': 'captured', 'key': 'wUKnWv', 'txnid': '1732986524646', 'transaction_fee': '1000.00', 'amount': '1000.00', 'cardCategory': 'domestic', 'discount': '0.00', 'addedon': '2024-11-30 22:38:58', 'productinfo': 'Self-Dancing', 'firstname': 'Ajay Verma', 'email': 'ajayverma6367006928@gmail.com', 'phone': '6367006928', 'hash': '3a3eff65867cdc870c71a54a044dfa6884864f427b39a8f246fb99937c4186da974b2864f0cdde1fe06c5fc364d4ecab1da1c372e336c76d749384fa8a7f69f4', 'field1': 776896113806089700, 'field2': 793431, 'field3': '1000.00', 'field5': '00', 'field6': '02', 'field7': 'AUTHPOSITIVE', 'field8': 'AUTHORIZED', 'field9': 'Transaction is Successful', 'payment_source': 'payu', 'PG_TYPE': 'CC-PG', 'bank_ref_no': 776896113806089700, 'ibibo_code': 'CC', 'error_code': 'E000', 'Error_Message': 'No Error', 'card_no': 'XXXXXXXXXXXX2346', 'is_seamless': 1, 'surl': 'https://success-nine.vercel.app', 'furl': 'https://failure-kohl.vercel.app', 'competition': 1}