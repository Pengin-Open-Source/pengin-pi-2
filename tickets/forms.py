from django import forms
from main.models.users import User
from tickets.models import Ticket, TicketComment
from util.security.group_access import is_manager_of_this_role, get_validated_user_ids_with_access_to_group


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
                self.fields['owner'].queryset = self.populate_owner_field()
            else:
                self.fields['owner'].queryset = self.populate_owner_field(
                    self.instance.role)

    def populate_owner_field(self, role=None):
        if role is None:
            owner_picklist_options = self.fields['owner'].queryset = User.objects.none(
            )
        else:
            # print("Here's what I call the role: ",  role)
            allowed_user_ids = get_validated_user_ids_with_access_to_group(
                role)

            # get these ids in queryset form so I can use them
            # in a picklist
            owner_picklist_options = User.objects.filter(
                id__in=allowed_user_ids)

            print("Hey so what are my options")
            print(owner_picklist_options)

        return owner_picklist_options


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
