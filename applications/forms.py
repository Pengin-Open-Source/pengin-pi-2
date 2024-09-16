# applications/forms.py
from django import forms
from .models import Application

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['resume', 'cover_letter', 'message', 'location']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume and not resume.name.endswith(('.pdf', '.doc', '.docx')):
            raise forms.ValidationError('Invalid file type. Allowed formats: .pdf, .doc, .docx')
        return resume

    def clean_cover_letter(self):
        cover_letter = self.cleaned_data.get('cover_letter')
        if cover_letter and not cover_letter.name.endswith(('.pdf', '.doc', '.docx')):
            raise forms.ValidationError('Invalid file type. Allowed formats: .pdf, .doc, .docx')
        return cover_letter
