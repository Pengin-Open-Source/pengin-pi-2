from django import forms
from main.models.users import User
from tickets.models import Ticket, TicketComment
from django.db.models import QuerySet


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

    def __init__(self, *args, can_set_ticket_owner_blank=True, role_options=None, owner_options=None, role_default=None, owner_default=None, **kwargs):
        super().__init__(*args, **kwargs)

        # I don't allow blank roles, so get rid of empty_label option:
        self.fields['role'].empty_label = None
        # assign the role options (mandatory) and owner options (optional)
        # to the dropdown picklists in the form.
        if role_options:
            self.fields['role'].queryset = role_options
        # Gemini's suggestion for avoiding treating an empty queryset as "None"
        if isinstance(owner_options, QuerySet):
            self.fields['owner'].queryset = owner_options
        # Creating a ticket should have default role of "default_ticket_support"
        # Editing should have default role of whatever was saved as the current role
        if role_default:
            self.fields['role'].initial = role_default
        # check flag to determine if the user
        # has permission to assign owner to *no one*
        # if not, get rid of  the "--------"  option.
        # and set the initial value to the owner_default
        if not can_set_ticket_owner_blank:
            # ASSUMPTION: in this case owner_default
            # *should* never have a value of None.
            self.fields['owner'].empty_label = None
            self.fields['owner'].initial = owner_default


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


class TicketSettingsForm(forms.Form):
    show_all_users = forms.ChoiceField(
        label='Users Shown in Owner Dropdown list',
        choices=[(0, "Users Associated with Selected Role"),
                 (1, "All Validated Users"),]
    )
