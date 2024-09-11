# I tweaked Gemini's (https://gemini.google.com/) answer when prompted to make LoginRequiredMixin
# give a graceful block to unauthorized users.
# This simply redirects to the Login Page instead of showing a wall of error text

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin


class GracefulLoginRequiredMixin(LoginRequiredMixin):
    def handle_no_permission(self):
        login_url = reverse('login')
        return redirect(login_url)
