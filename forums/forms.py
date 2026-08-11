# forums/forms.py
from django import forms
from .models import Thread, ForumPost, ForumComment


class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['name']


class ForumPostForm(forms.ModelForm):
    class Meta:

        # I decided to put the selection choices in the form itself
        # Gemini's suggestion on how:
        resolution_status = forms.ChoiceField(
            choices=(
                ('open', 'Open'),
                ('closed', 'Closed'),
                ('resolved', 'Resolved'),
            ),
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        model = ForumPost
        fields = ['title', 'content', 'tags']


class ForumCommentForm(forms.ModelForm):
    class Meta:
        model = ForumComment
        fields = ['content']
