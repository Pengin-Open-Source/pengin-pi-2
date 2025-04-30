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

        if self.instance and not self.instance._state.adding:
            allowed_user_ids = get_validated_user_ids_with_access_to_group(
                self.instance.role)

            # get these ids in queryset form so I can use them
            # in a picklist
            owner_picklist_ids = User.objects.filter(
                id__in=allowed_user_ids).values_list('id', flat=True)
            print(owner_picklist_ids)
            # print("Here are the fields")
            # print(self.fields)
            self.fields['owner'].queryset = owner_picklist_ids


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
