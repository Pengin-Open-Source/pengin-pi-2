from django import forms

from .models import Contract


class ContractForm(forms.ModelForm):

    class Meta:
        model = Contract
        fields = ['customer', 'type', 'content', 'service_date', 'expiration_date',]