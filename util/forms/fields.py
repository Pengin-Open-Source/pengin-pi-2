from django import forms

# items being reused in multiple apps and forms.


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name
