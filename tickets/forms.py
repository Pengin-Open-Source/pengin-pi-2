from django import forms
from main.models.users import User
from tickets.models import Ticket, TicketComment
from util.security.group_access import get_valid_users_with_rbac


# Same technique as in Events
class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class TicketForm(forms.ModelForm):

    owner = UserModelChoiceField(
        queryset=User.objects.filter(validated=True), required=False)

    class Meta:
        model = Ticket
        fields = ['summary', 'role', 'owner', 'content', 'tags']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # print("Here's the ticket")
        # print(kwargs.get('instance').role)
        # print(self.instance.role)

        if self.instance:
            if self.instance._state.adding:
                self.fields['owner'].queryset = get_valid_users_with_rbac()
            else:
                self.fields['owner'].queryset = get_valid_users_with_rbac(
                    self.instance.role)


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
