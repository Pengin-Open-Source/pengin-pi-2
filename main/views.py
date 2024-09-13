# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from util.mail import send_mail
from django.utils.decorators import method_decorator
from django.views import View
from .forms import LoginForm, SignUpForm, PasswordResetForm, SetPasswordForm
from .models.users import User
from datetime import datetime, timedelta
import uuid
from django_ratelimit.decorators import ratelimit
import os


def generate_uuid():
    return str(uuid.uuid4())


class LoginView(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'authentication/login.html', {'form': form, 'primary_title': 'Login'})

    # @ratelimit(key='ip', rate='3/minute', block=True)
    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home_view')
        messages.error(
            request, 'Please check your login details and try again.')
        return redirect('login')


class SignupView(View):
    def get(self, request):
        form = SignUpForm()
        return render(request, 'authentication/signup.html', {'form': form, 'primary_title': 'Sign Up', 'site_key': os.getenv("SITE_KEY")})

    # @ratelimit(key='ip', rate='3/minute', block=True)
    def post(self, request):
        # Access request object through self.request
        form = SignUpForm(self.request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.validation_date = datetime.utcnow()
            user.save()
            send_mail(user.email, user.validation_id, "user_validation")
            return redirect('login')
        messages.error(
            self.request, 'Email address already exists or invalid email.')
        return redirect('signup')


class LogoutView(View):
    @method_decorator(login_required)
    def get(self, request):
        logout(request)
        return redirect('home_view')

      
class PasswordResetRequestView(View):
    def get(self, request):
        form = PasswordResetForm()
        return render(request, 'authentication/generate_prt_form.html', {'form': form, 'primary_title': 'Forgot Password', 'site_key': os.getenv("SITE_KEY")})

    # @ratelimit(key='ip', rate='3/minute', block=True)
    def post(self, request):
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email=email).first()
            if user:
                if user.validated:
                    user.prt = generate_uuid()
                    user.prt_reset_date = datetime.utcnow()
                    user.save()
                    send_mail(user.email, user.prt, "password_reset")
                    return redirect('login')
                messages.error(request, 'This account is not validated.')
            else:
                messages.error(request, 'Email does not exist.')
        return redirect('generate_prt')


class PasswordResetView(View):
    def get(self, request, token):
        user = User.objects.filter(prt=token).first()
        if user:
            form = SetPasswordForm()
            return render(request, 'authentication/reset_password_form.html', {'form': form, 'email': user.email, 'token': token, 'site_key': os.getenv("SITE_KEY"), 'primary_title': 'Reset Password'})
        return redirect('generate_prt')

    # @ratelimit(key='ip', rate='3/minute', block=True)
    def post(self, request, token):
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            email = request.POST.get('email')
            new_password = form.cleaned_data['new_password']
            confirm_new_password = form.cleaned_data['confirm_new_password']
            user = User.objects.filter(email=email).first()
            if user and new_password == confirm_new_password:
                if datetime.utcnow() > user.prt_reset_date + timedelta(minutes=60):
                    messages.error(request, 'Token expired.')
                else:
                    user.prt_consumption_date = datetime.utcnow()
                    user.set_password(new_password)
                    user.save()
                    return redirect('login')
            else:
                messages.error(request, 'Passwords do not match.')
        return redirect('reset_password', token=token)
