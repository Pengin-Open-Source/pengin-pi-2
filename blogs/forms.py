# blogs/forms.py

from django import forms
from blogs.models import BlogPost


class BlogForm(forms.ModelForm):

    # Set values for fields,  - useful when you want
    # to add in new fields that weren't included in the form
    # and wouldn't have gone through form validation.
    # For example, in blogs, don't need the Method field to
    # ever be on the template version of the form,  and I don't
    # want users to be able to edit the date of the blog post.
    def set_cleaned_data_field(self, field, value):
        # if we ever need validation logic... can
        # check here
        self.cleaned_data[field] = value

    class Meta:
        model = BlogPost
        fields = ['title',
                  'content', 'tags']
        widgets = {'content': forms.Textarea(attrs={'cols': 120, 'rows': 40})}
