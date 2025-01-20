from django_flatpickr.widgets import DateTimePickerInput
from django import forms
from main.models import User
from .models import Event, EventParticipant


# Credit to https://stackoverflow.com/questions/49114304/to-field-name-argument-on-a-modelchoicefield-doesnt-seem-to-be-working
# -> Alasdair's answer, Plus help from Google Gemini on how to get the selection box to display User names instead of emails without
# changing the User __str__ method.
class UserModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class EventForm(forms.ModelForm):
    participants = UserModelMultipleChoiceField(
        queryset=User.objects.all(), required=False)
    organizer = UserModelChoiceField(queryset=User.objects.all())

    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "location",
            "start_datetime",
            "end_datetime",
            "organizer",
            "participants",
            "roles",
        ]

        widgets = {
            "start_datetime": DateTimePickerInput(),
            "end_datetime": DateTimePickerInput(),
        }

    def clean(self):
        cleaned_up_data = super().clean()
        selected_participants = cleaned_up_data.get('participants')
        print("End User Selected these Participants just now")
        print(selected_participants)

        # I want compare the selected_participants to the ones
        # currently in the database - if any for this event - and create and delete participants as needed.
        if self.instance:
            current_participants_ids = EventParticipant.objects.filter(
                event_id=self.instance.id).values_list('participant_id', flat=True)
            # get the User Objects for the Event Participants

            current_participants = User.objects.filter(
                id__in=current_participants_ids)
            self.participants_to_add = selected_participants.exclude(
                id__in=current_participants)
            self.delete_participants = current_participants.exclude(
                id__in=selected_participants)
        else:
            self.participants = selected_participants

        return cleaned_up_data


class CalendarSettingsForm(forms.Form):
    first_day_of_week = forms.ChoiceField(
        label='First Day of the Calendar Week',
        choices=[(6, "Sunday"), (0, "Monday"),]
    )
