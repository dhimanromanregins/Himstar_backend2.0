from django.contrib import admin
from .models import Category, Competition, CompetitionMedia, Round, Tournament, PrizeBreakdown
from .forms import TournamentAdminForm


admin.site.register(Category)
admin.site.register(CompetitionMedia)
admin.site.register(Round)
admin.site.register(PrizeBreakdown)


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    # Display these fields in the list view
    list_display = (
        'unique_id',
        'name',
        'start_date',
        'end_date',
        'competition_type',
        'is_active',
        'winning_price',
        'max_participants',
        'category'
    )

    # Add filters to the sidebar
    list_filter = (
        'competition_type',
        'is_active',
        'start_date',
        'end_date',
        'registration_open_date',
        'registration_close_date',
        'category'
    )

    # Enable search for these fields
    search_fields = (
        'unique_id',
        'name',
        'location',
        'description',
        'rules'
    )

    # Optionally add date hierarchy for the start date
    date_hierarchy = 'start_date'

# @admin.register(Tournament)
# class TournamentAdmin(admin.ModelAdmin):
#     readonly_fields = ('file_uri',)

class TournamentAdmin(admin.ModelAdmin):
    form = TournamentAdminForm

# admin.site.register(Tournament, TournamentAdmin)

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    # Display these fields in the list view

    form = TournamentAdminForm
    list_display = (
        'unique_id',
        'name',
        'start_date',
        'end_date',
        'category',
        'is_active',
        'max_participants',
        'winning_price'
    )

    # Add filters to the sidebar
    list_filter = (
        'is_active',
        'start_date',
        'end_date',
        'registration_open_date',
        'registration_close_date',
        'category'
    )

    # Enable search for these fields
    search_fields = (
        'unique_id',
        'name',
        'description',
        'rules',
        'file_uri'
    )

    # Optionally add date hierarchy for the start date
    date_hierarchy = 'start_date'


