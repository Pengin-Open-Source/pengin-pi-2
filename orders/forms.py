from django import forms
from django.core.exceptions import ValidationError
from .models import Order, Customer


class OrderForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ['order_date', 'customer',]


class CustomerForm(forms.ModelForm):

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        company = cleaned_data.get('company')
        if user and company:
            raise ValidationError('Customer cannot have both user and company relationships.')
        if not user and not company:
            raise ValidationError('Customer must have either a user or a company relationship.')

    class Meta:
        model = Customer
        fields = ['user', 'company',]