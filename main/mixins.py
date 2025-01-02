# Reworked Gemini's (https://gemini.google.com/) answers for making LoginRequiredMixin
# give a graceful block to unauthorized users and adding on new constraints to login required.


from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin


class LoginAndValidationRequiredMixin(LoginRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.validated:
                return super().dispatch(request, *args, **kwargs)
            # Else if logged in but not validated
            return HttpResponseForbidden("<h1> Your Account Must Be Validated Before You Can Access This Page. </h1>")

        # Else if not authenticated
        login_url = reverse('login')
        return redirect(login_url)
