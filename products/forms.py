# products/forms.py
from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    file_large = forms.FileField(required=False)
    file_small = forms.FileField(required=False)

    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'tags', 'file_large', 'file_small']
