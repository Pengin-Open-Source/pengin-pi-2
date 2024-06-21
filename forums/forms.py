# forums/forms.py
from django import forms
from .models import Thread, ForumPost, ForumComment

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['name']

class ForumPostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ['title', 'content', 'tags']

class ForumCommentForm(forms.ModelForm):
    class Meta:
        model = ForumComment
        fields = ['content']
