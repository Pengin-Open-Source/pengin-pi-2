from django import forms
from .models import Company, CompanyMembers

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'address1', 'address2', 'city', 'state', 'zipcode', 'country', 'phone', 'email']


class CompanyMembersForm(forms.ModelForm):
    class Meta:
        model = CompanyMembers
        fields = ['user'] 