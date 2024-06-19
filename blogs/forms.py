# blogs/forms.py

from django import forms
from blogs.models import BlogPost


class BlogForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        # LIST of fields to hide.
        # Don't make it an attribute of BlogForm,  we don't want these fields in the template at all
        # and the form gets passed to the template
        remove_fields = kwargs.pop('remove_fields', [])
        # DICT with fields to prefill and their prefill data
        self.prefill_data = kwargs.pop('prefill_data', {})
        super().__init__(*args, **kwargs)

        # It only makes sense to remove populate the data once we remove the fields
        for field in remove_fields:
            self.fields.pop(field)

        for field_name,  value in self.prefill_data.items():
            if field_name in self.fields:
                self.initial[field_name] = value

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
        fields = ['title',  'author', 'edited_by',
                  'date',  'content', 'tags']
        widgets = {'content': forms.Textarea(attrs={'cols': 120, 'rows': 40}), 'author': forms.TextInput(
            attrs={'readonly': 'readonly'}), 'edited_by': forms.TextInput(attrs={'readonly': 'readonly'}), 'date': forms.TextInput(attrs={'readonly': 'readonly'})}
