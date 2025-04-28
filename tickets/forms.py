from django import forms
from tickets.models import Ticket, TicketComment
from util.security.group_access import is_manager_of_this_role, get_validated_users_with_access_to_group


class TicketForm(forms.ModelForm):

    class Meta:
        model = Ticket
        fields = ['summary', 'role', 'owner', 'content', 'tags']


class TicketEditStatusForm(forms.ModelForm):
   # I decided to put the selection choices in the form itself
   # Gemini's suggestion on how:
    resolution_status = forms.ChoiceField(
        choices=(
                ('open', 'Open'),
                ('closed', 'Closed'),
                ('resolved', 'Resolved'),
        ),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Ticket
        fields = ['resolution_status']


class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ['content']
