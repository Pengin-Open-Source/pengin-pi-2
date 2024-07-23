# forms.py
from django import forms
from .models import Job

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['job_title', 'short_description', 'long_description', 'department', 'salary', 'location', 'hiring_manager']
        widgets = {
            'short_description': forms.TextInput(attrs={'placeholder': 'Write a brief description'}),
            # Add other widget customizations if needed
        }
