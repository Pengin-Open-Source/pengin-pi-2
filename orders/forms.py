from django import forms
from django.core.exceptions import ValidationError
from .models import Order, Customer


class OrderForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ['order_date', 'customer',]


class CustomerForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = ['user', 'company',]