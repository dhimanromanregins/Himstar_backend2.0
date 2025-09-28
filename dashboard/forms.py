from django import forms
from .models import Tournament, Competition

class TournamentAdminForm(forms.ModelForm):
    class Meta:
        model = Tournament
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['competitions'].queryset = Competition.objects.filter(competition_type=Competition.TOURNAMENT)
