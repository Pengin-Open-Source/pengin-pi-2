# blogs/forms.py

from django import forms
from blogs.models import BlogPost


class BlogForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        # LIST of fields to hide
        self.hide_fields = kwargs.pop('hide_fields', [])
        # DICT with fields to prefill and their prefill data
        self.prefill_data = kwargs.pop('prefill_data', {})
        super().__init__(*args, **kwargs)

        # Prefill fields with data - we don't care at this point
        # whether the fields will actually show in the form.
        # If they don't show,  they'll still have their data
        # filled  and ready for the form.save()
        for field_name,  value in self.prefill_data.items():
            if field_name in self.fields:
                self.initial[field_name] = value

        self.fields = {
            field for field in self.fields if field not in self.hide_fields}

    class Meta:
        model = BlogPost
        fields = ['title',  'author', 'edited_by',
                  'date',  'content', 'tags',  'method']
        widgets = {'content': forms.Textarea(
            attrs={'cols': 120, 'rows': 40}), }
