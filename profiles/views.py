from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.db.models.functions import Lower
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail  # Assumes send_mail is correctly set up
from django.http import HttpResponseForbidden
from datetime import timedelta
from django.conf import settings
from main.mixins import LoginAndValidationRequiredMixin
from util.security.group_access import get_all_groups_for_user_with_extended_rbac, get_groups_user_manages
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
        can_re_validate = not request.user.self_validated and now > delta
        context = {
            'name': request.user.name,
            'email': request.user.email,
            'can_do': can_re_validate,
            'primary_title': 'Profile Information',
            'is_admin': request.user.is_staff
        }
        return render(request, 'profile.html', context)


@method_decorator(login_required, name='dispatch')
class SendEmailView(LoginRequiredMixin, View):
    def get(self, request):
        now = timezone.now()
        user = request.user
        # NOTE validation date probably needs be renamed to sign up date
        # or used differently.
        delta = user.validation_date + timedelta(minutes=5)
        if not user.self_validated and now > delta:
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
        if not request.user.is_authenticated:
            login_url = reverse('login')
            return redirect(f"{login_url}?next={request.path}")
        user = User.objects.filter(validation_id=token).first()
        if user:
            if user == request.user:

                user.self_validated = True
                if settings.ENABLE_USER_SELF_VALIDATION is True:
                    user.validated = True
                    return_template = 'user_validated.html'
                else:
                    return_template = 'user_pre_validated.html'

                user.save()
                return render(request, return_template, {})
            else:
                return HttpResponseForbidden("<h1> Expired, Unauthorized, or Invalid link for the current user. </h1>")
        else:
            return HttpResponseForbidden("<h1> Expired, Unauthorized, or Invalid link for the current user. </h1>")


@method_decorator(login_required, name='dispatch')
class EditProfileView(LoginRequiredMixin, View):
    def get(self, request):
        form = EditProfileForm(instance=request.user)
        return render(request, 'profile_edit.html', {
            'form': form,
            'primary_title': 'Edit Profile'
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
            'primary_title': 'Edit Password'
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


class UserGroupListView(LoginAndValidationRequiredMixin, View):

    template_name = "user_group_list.html"

    def get(self, request, *args, **kwargs):
        group_filter = self.kwargs.get('group_filter')
        if group_filter is None:
            group_filter = 'member_of'
        user_to_check = request.user
        # TODO If list of members gets in the 1000s
        # and performance may suffer. In that case,
        # consider replacing Lower() call with some
        # other strategy,  like a lowercase name
        # field in the database.

        # TODO - differentiate between types of Group memberships:
        # Direct,  Inherited, and non-tree Group-to-Group access
        if group_filter == 'member_of':
            group_list = get_all_groups_for_user_with_extended_rbac(
                user_to_check).order_by(Lower('name'))
        elif group_filter == 'manager_of':
            group_list = get_groups_user_manages(
                user_to_check).order_by(Lower('name'))
        else:
            # this should never be hit,  but leave it here as placeholder for the TODO above
            group_list = []

        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(group_list, 10)
        page_obj = paginator.get_page(page_number)
        context = {}

        context['page_obj'] = page_obj

        context['primary_title'] = "Groups For " + user_to_check.name
        return render(request, self.template_name, context)
