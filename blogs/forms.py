# blogs/forms.py

from django import forms
from blogs.models import BlogPost


class BlogForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title',  'author', 'edited_by',
                  'date',  'content', 'tags',  'method']
        widgets = {'content': forms.Textarea(
            attrs={'cols': 120, 'rows': 40}), }
