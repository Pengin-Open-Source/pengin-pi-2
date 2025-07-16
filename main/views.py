# views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from util.security.group_access import get_cross_group_access, get_direct_children_of_group, get_direct_parent, get_users_with_extended_rbac_to_group
from main.mixins import LoginAndValidationRequiredMixin
from util.mail import send_mail
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.views import View
from .forms import GroupForm, GroupManagerForm, LoginForm, SignUpForm, PasswordResetForm, SetPasswordForm
from .models.users import Group, GroupManager, User
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


# Group/Role Management

class GroupListView(LoginAndValidationRequiredMixin,  UserPassesTestMixin, View):

    template_name = "management/groups.html"

    def get(self, request, *args, **kwargs):

        groups = Group.objects.all().order_by('name')

        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(groups, 10)
        page_obj = paginator.get_page(page_number)
        context = {}
        context['is_admin'] = request.user.is_staff
        context['page_obj'] = page_obj

        return render(request, self.template_name, context)

    def test_func(self):
        return self.request.user.is_staff


class GroupDetailView(LoginAndValidationRequiredMixin,  UserPassesTestMixin, View):

    template_name = "management/group_detail.html"

    def get(self, request, *args, **kwargs):

        group = get_object_or_404(Group, id=self.kwargs.get('pk'))
        group_manager = GroupManager.objects.filter(
            managed_group=group).first()

        context = {}
        if group_manager:
            manager_form = GroupManagerForm(instance=group_manager)
        else:
            manager_form = GroupManagerForm()

        for field in manager_form.fields:
            manager_form.fields[field].widget.attrs['disabled'] = True
        form = GroupForm(instance=group)

        for field in form.fields:
            form.fields[field].widget.attrs['disabled'] = True
        parent = get_direct_parent(group)

        context['parent_group'] = parent
        context['group'] = group
        context['manager_form'] = manager_form
        context['form'] = form
        context['is_admin'] = request.user.is_staff

        return render(request, self.template_name, context)

    def test_func(self):
        return self.request.user.is_staff


class GroupChildListDetailView(LoginAndValidationRequiredMixin,  UserPassesTestMixin, View):

    template_name = "management/group_children_detail.html"

    def get(self, request, *args, **kwargs):

        parent_group = get_object_or_404(Group, id=self.kwargs.get('pk'))
        child_groups = get_direct_children_of_group(parent_group)

        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(child_groups, 10)
        page_obj = paginator.get_page(page_number)
        context = {}
        context['is_admin'] = request.user.is_staff
        context['page_obj'] = page_obj
        context['parent_group'] = parent_group
        return render(request, self.template_name, context)

    def test_func(self):
        return self.request.user.is_staff


class NonHierarchicalAccessGroupListDetailView(LoginAndValidationRequiredMixin,  UserPassesTestMixin, View):

    template_name = "management/groups_non_tree_access.html"

    def get(self, request, *args, **kwargs):

        group_with_access = get_object_or_404(Group, id=self.kwargs.get('pk'))
        accesible_groups = get_cross_group_access({group_with_access})

        accesible_group_list = [id['accessed_group']
                                for id in accesible_groups]
        accessed_groups = Group.objects.filter(
            id__in=accesible_group_list)

        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(accessed_groups, 10)
        page_obj = paginator.get_page(page_number)
        context = {}
        context['is_admin'] = request.user.is_staff
        context['page_obj'] = page_obj
        context['group_with_access'] = group_with_access
        return render(request, self.template_name, context)

    def test_func(self):
        return self.request.user.is_staff


class GroupMemberListView(LoginAndValidationRequiredMixin,  UserPassesTestMixin, View):

    template_name = "management/group_member_list.html"

    def get(self, request, *args, **kwargs):

        group = get_object_or_404(Group, id=self.kwargs.get('pk'))
        users_in_group = get_users_with_extended_rbac_to_group(group)

        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(users_in_group, 10)
        page_obj = paginator.get_page(page_number)
        context = {}
        context['is_admin'] = request.user.is_staff
        context['page_obj'] = page_obj
        context['group'] = group

        return render(request, self.template_name, context)

    def test_func(self):
        return self.request.user.is_staff
