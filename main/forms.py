# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models.users import User, Group, GroupManager


class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False)


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'name', 'password1', 'password2']


class PasswordResetForm(forms.Form):
    email = forms.EmailField()


class SetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_new_password = forms.CharField(widget=forms.PasswordInput)


class GroupManagerForm(forms.ModelForm):
    class Meta:
        model = GroupManager
        fields = ['manager', 'managed_group']


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
