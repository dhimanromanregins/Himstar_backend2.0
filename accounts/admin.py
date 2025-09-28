from django.contrib import admin
from .models import Register, OTP, Awards, Referral, ReferralReward
# Register your models here.

@admin.register(Register)
class RegisterAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = (
        'user',
        'custom_id',
        'phonenumber',
        'zipcode',
        'gender',
        'dob',
        'points',
        'votes'
    )

    # Add filters to the sidebar
    list_filter = ('gender', 'dob', 'points', 'votes')

    # Enable search for these fields
    search_fields = ('user__username', 'custom_id', 'phonenumber', 'zipcode')

    readonly_fields = ('referral_code', )

    # Optionally add date hierarchy for the Date of Birth field
    date_hierarchy = 'dob'
admin.site.register(Awards)
admin.site.register(OTP)
admin.site.register(Referral)

@admin.register(ReferralReward)
class ReferralRewardAdmin(admin.ModelAdmin):
    list_display = ('amount', 'last_updated')
    search_fields = ('amount',)
