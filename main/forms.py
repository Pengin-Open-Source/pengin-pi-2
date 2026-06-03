# forms.py
from django import forms
from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models.users import User, Group, GroupManager
from util.forms.fields import UserModelChoiceField


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

    manager = UserModelChoiceField(
        queryset=User.objects.filter(validated=True), required=False)

    class Meta:
        model = GroupManager
        fields = ['manager']


class GroupManagerDjangoSiteForm(forms.ModelForm):

    manager = UserModelChoiceField(
        queryset=User.objects.filter(validated=True), required=False)

    class Meta:
        model = GroupManager
        fields = '__all__'


class GroupManagerDjangoSiteFormAdmin(admin.ModelAdmin):
    form = GroupManagerDjangoSiteForm

# Suggestion from Gemini on how to Force un-validation
# of a User if the SuperUser inactivates it.
# They way the SuperUser doesn't have to know/remember
# to uncheck two boxes


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

        labels = {
            'is_active': 'User is Active?  (If Unchecked, "Validated" will be auto-unchecked upon Save)',
            'is_staff': 'Staff/Admin Level Access? (Cannot be checked if User is not Active & Validated)',
            # You can even use help_text to be even more descriptive
        }

    def clean(self):
        cleaned_data = super().clean()

        # Get the current form states for both fields
        is_active = cleaned_data.get('is_active')

        is_validated = cleaned_data.get('validated')

        is_staff = cleaned_data.get('is_staff')

        # The Pre-Database Kill Switch:
        # If the user is being deactivated, automatically turn off the validation flag.
        if is_active is False and is_validated is True:
            cleaned_data['validated'] = False

        if is_staff and (not is_validated or not is_active):
            raise forms.ValidationError({
                "Cannot invalidate or inactivate Staff.  Remove Staff status first"
            })

        # if this is a staff user,  don't allow

        return cleaned_data


class GroupForm(forms.ModelForm):

    class Meta:
        model = Group
        fields = ['name']
