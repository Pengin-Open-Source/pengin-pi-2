from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail  # Assumes send_mail is correctly set up
from django.http import Http404
from datetime import timedelta
from .forms import EditProfileForm, EditPasswordForm
# Removed import for Role and UserRoles as they do not exist
# Correctly import User from the main app
from main.models.users import User
import uuid

# Example utility function if generate_uuid is required


def generate_uuid():
    return str(uuid.uuid4())


@method_decorator(login_required, name='dispatch')
class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        now = timezone.now()
        delta = request.user.validation_date + timedelta(minutes=5)
        can_re_validate = not request.user.validated and now > delta
        context = {
            'name': request.user.name,
            'email': request.user.email,
            'can_do': can_re_validate,
            'primary_title': 'Profile Information',
            'is_admin': self.request.user.validated and self.request.user.is_staff
        }
        return render(request, 'profile.html', context)


@method_decorator(login_required, name='dispatch')
class SendEmailView(LoginRequiredMixin, View):
    def get(self, request):
        now = timezone.now()
        user = request.user
        delta = user.validation_date + timedelta(minutes=5)
        if not user.validated and now > delta:
            user.validation_date = now
            # Assuming generate_uuid generates a unique identifier
            user.validation_id = generate_uuid()
            user.save()
            send_mail(
                'Validate Your Account',
                f'Your validation token is: {user.validation_id}',
                'from@example.com',  # Use your configured sender email
                [user.email],
            )
        return redirect('profiles:profile')


class ValidateView(View):
    def get(self, request, token):
        try:
            user = User.objects.filter(validation_id=token).first()
            if user:
                user.validated = True
                # Assuming you might want to add the user to a default group instead
                user.save()
                return redirect('profiles:profile')
            else:
                raise Http404("User not found.")
        except User.DoesNotExist:
            raise Http404("User not found.")


@method_decorator(login_required, name='dispatch')
class EditProfileView(LoginRequiredMixin, View):
    def get(self, request):
        form = EditProfileForm(instance=request.user)
        return render(request, 'profile_edit.html', {
            'form': form,
            'primary_title': 'Edit Profile',
            'is_admin': self.request.user.validated and self.request.user.is_staff
        })

    def post(self, request):
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profiles:profile')
        return render(request, 'profile_edit.html', {
            'form': form,
            'primary_title': 'Edit Profile'
        })


@method_decorator(login_required, name='dispatch')
class EditPasswordView(LoginRequiredMixin, View):
    def get(self, request):
        form = EditPasswordForm()
        return render(request, 'password_edit.html', {
            'form': form,
            'primary_title': 'Edit Password',
            'is_admin': self.request.user.validated and self.request.user.is_staff
        })

    def post(self, request):
        form = EditPasswordForm(request.POST)
        if form.is_valid():
            old_password = form.cleaned_data.get('curr_password')
            new_password = form.cleaned_data.get('new_password')
            confirm_new_password = form.cleaned_data.get(
                'confirm_new_password')
            if new_password == confirm_new_password:
                if check_password(request.user.password, old_password):
                    request.user.password = make_password(new_password)
                    request.user.save()
                    return redirect('profiles:profile')
            messages.error(request, 'Please check your password details.')
        return render(request, 'password_edit.html', {
            'form': form,
            'primary_title': 'Edit Password'
        })
