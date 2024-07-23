# forms.py
from django import forms
from .models import Home

class HomeForm(forms.ModelForm):
    image = forms.ImageField(required=False)
    
    class Meta:
        model = Home
        fields = ['company_name', 'article', 'tags', 'image']
        widgets = {
            'article': forms.Textarea(attrs={'placeholder': 'Write about your organization here.'}),
            'tags': forms.TextInput(attrs={'placeholder': 'tags,tags'}),
        }