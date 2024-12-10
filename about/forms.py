from django import forms
from .models import About

class AboutForm(forms.ModelForm):
    image = forms.ImageField(required=False)

    class Meta:
        model = About
        fields = [
            'name', 'article', 'facebook', 'instagram', 'whatsapp',
            'linkedin', 'youtube', 'twitter', 'phone', 'address1', 'address2',
            'city', 'state', 'country', 'tags', 'image'  # Corrected 'state' field
        ]
        widgets = {
            'article': forms.Textarea(attrs={'placeholder': 'Write about your organization here.'}),
            'tags': forms.TextInput(attrs={'placeholder': 'tags,tags'}),
            # Add other widget customizations if needed
        }
    
    def __init__(self, *args, **kwargs):
        super(AboutForm, self).__init__(*args, **kwargs)
        # Make specific fields optional
        optional_fields = [
            'facebook', 'instagram', 'whatsapp', 'linkedin', 
            'youtube', 'twitter', 'phone', 'address1', 
            'address2', 'city', 'state', 'country', 'tags', 'image'
        ]
        for field in optional_fields:
            self.fields[field].required = False
