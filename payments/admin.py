from django.contrib import admin
from .models import Account, PaymentDetails

# Register Account model
admin.site.register(Account)
# Customize the PaymentDetails admin
@admin.register(PaymentDetails)
class PaymentDetailsAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = (
        'txnid',
        'amount',
        'mode',
        'productinfo',
        'firstname',
        'email',
        'status',
        'created_at'
    )

    # Add filters to the sidebar
    list_filter = (
        'mode',
        'status',
        'created_at',
        'cardCategory',
        'competition',
        'tournament'
    )
    # Enable search for these fields
    search_fields = ('txnid', 'email', 'phone', 'firstname', 'productinfo')
    # Optionally add date hierarchy
    date_hierarchy = 'created_at'
