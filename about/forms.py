# forms.py
from django import forms
from .models import About

class AboutForm(forms.ModelForm):
    class Meta:
        model = About
        fields = [
            'name', 'article', 'facebook', 'instagram', 'whatsapp',
            'linkedin', 'youtube', 'twitter', 'phone', 'address1', 'address2',
            'city', 'state', 'country', 'tags', 'image'
        ]
        widgets = {
            'article': forms.Textarea(attrs={'placeholder': 'Write about your organization here.'}),
            'tags': forms.TextInput(attrs={'placeholder': 'tags,tags'}),
            # Add other widget customizations if needed
        }

    image = forms.ImageField(required=False)
