from django import forms

from .models import Contract


class ContractForm(forms.ModelForm):

    service_date = forms.DateField(widget=forms.SelectDateWidget)
    expiration_date = forms.DateField(widget=forms.SelectDateWidget)

    class Meta:
        model = Contract
        fields = ['customer', 'type', 'content', 'service_date', 'expiration_date',]