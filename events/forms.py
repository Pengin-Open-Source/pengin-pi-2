from django_flatpickr.widgets import DateTimePickerInput
from django import forms
from main.models import User
from .models import Event


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
    participants = UserModelMultipleChoiceField(queryset=User.objects.all())
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


class CalendarSettingsForm(forms.Form):
    first_day_of_week = forms.ChoiceField(
        label='First Day of the Calendar Week',
        choices=[(6, "Sunday"), (0, "Monday"),]
    )
