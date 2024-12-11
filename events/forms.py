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
            "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"})
        }
