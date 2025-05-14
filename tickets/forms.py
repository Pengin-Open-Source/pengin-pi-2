from django import forms
from main.models.users import User
from tickets.models import Ticket, TicketComment


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

    def __init__(self, role_options, owner_options, role_default=None,   *args, **kwargs):
        super().__init__(*args, **kwargs)

        # I don't allow blank roles, so get rid of empty_label option:
        self.fields['role'].empty_label = None
        # assign the role options (mandatory) and owner options (optional)
        # to the dropdown picklists in the form.
        self.fields['role'].queryset = role_options
        self.fields['owner'].queryset = owner_options

        # if we are adding a ticket,  set it to the default role supplied
        if self.instance and self.instance._state.adding:
            self.fields['role'].initial = role_default


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
