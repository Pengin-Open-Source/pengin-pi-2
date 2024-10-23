import json
from uuid import UUID
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Company, CompanyMembers
from main.models.users import User
from .forms import CompanyForm
from django_ratelimit.decorators import ratelimit
from django.contrib.auth.mixins import UserPassesTestMixin
from main.mixins import LoginAndValidationRequiredMixin


class CompaniesHomeView(LoginAndValidationRequiredMixin,  View):

    def get(self, request):
        if request.user.is_staff:
            return redirect('companies_list')
        else:
            member_companies = CompanyMembers.objects.filter(
                user_id=request.user.id)
            if member_companies and member_companies.count() > 1:
                return redirect('companies_list')
            else:
                member_company = member_companies.first()
            if member_company:
                return redirect('display_company_info', pk=member_company.company_id)
            return render(request, 'no_company.html')


class CompaniesListView(LoginAndValidationRequiredMixin,  ListView):

    queryset = Company.objects.all()
    template_name = 'company_info_main.html'
    model = Company
    context_object_name = 'companies'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_staff:
            companies = Company.objects.all()
        else:
            company_ids = CompanyMembers.objects.filter(
                user_id=self.request.user.id).values_list('company_id', flat=True)
            company_ids_list = list(company_ids)
            companies = Company.objects.filter(id__in=company_ids_list)

        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(companies, 10)
        page_obj = paginator.get_page(page_number)
        context['companies'] = page_obj
        context['is_admin'] = self.request.user.is_staff
        context['primary_title'] = 'Companies'

        return context


class CompanyDetailView(LoginAndValidationRequiredMixin, UserPassesTestMixin, DetailView):
    model = Company
    template_name = 'company_info.html'
    context_object_name = 'company'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        company = self.get_object()
        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        members_ids = CompanyMembers.objects.filter(
            company_id=company.id).values_list('user_id', flat=True)
        users = User.objects.filter(id__in=members_ids)
        paginator = Paginator(users.order_by('name'), 10)  # 10 users per page
        page_obj = paginator.get_page(page_number)

        is_admin = self.request.user.is_staff
        context['is_admin'] = is_admin
        context['users'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['primary_title'] = 'Company Info'
        context['company'] = company
        return context

    def test_func(self):
        if self.request.user.is_staff:
            return True

        company = self.get_object()
        company_member = CompanyMembers.objects.filter(
            user_id=self.request.user.id, company_id=company.id)

        # if company_member is "truthy"/exists, let the member see the Company Info
        if company_member:
            return True
        return False


class CompanyCreateView(LoginAndValidationRequiredMixin, UserPassesTestMixin, CreateView):

    model = Company
    form_class = CompanyForm
    template_name = 'company_create.html'

    def get(self, request, *args, **kwargs):
        form = CompanyForm()
        form_rendered_for_create = form.render("configure_company_form.html")
        context = {'form': form_rendered_for_create,
                   'primary_title': 'Create New Company'}
        return render(request, self.template_name,  context)

    def post(self, request):
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.created_by = request.user
            company.row_action = 'CREATE'
            company.save()
            CompanyMembers.objects.create(company=company, user=request.user)
            return redirect('display_company_info', pk=company.id)

    # only staff can create companies
    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False


class CompanyEditView(LoginAndValidationRequiredMixin, UserPassesTestMixin, UpdateView):

    model = Company
    form_class = CompanyForm
    template_name = 'company_edit.html'

    def get_context_data(self,  **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.get_object()
        form = CompanyForm(instance=company)
        form_rendered_for_edit = form.render("configure_company_form.html")
        context['form'] = form_rendered_for_edit
        context['primary_title'] = 'Edit Company'
        return context

    def post(self, request, *args, **kwargs):
        company = self.get_object()
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            company = form.save(commit=False)
            company.user = request.user
            company.row_action = 'EDIT'
            company.date = timezone.now()
            company.save()
            return redirect('display_company_info', pk=company.id)

    # only staff can Edit companies
    def test_func(self):
        if self.request.user.is_staff:
            return True
        return False


class CompanyMembersListDetailView(LoginAndValidationRequiredMixin, UserPassesTestMixin, DetailView):
    model = Company
    template_name = 'display_members.html'
    context_object_name = 'company'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        company = self.get_object()
        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        members_ids = CompanyMembers.objects.filter(
            company_id=company.id).values_list('user_id', flat=True)
        users = User.objects.filter(id__in=members_ids)
        paginator = Paginator(users.order_by('name'), 10)  # 10 users per page
        page_obj = paginator.get_page(page_number)

        is_admin = self.request.user.is_staff
        context['is_admin'] = is_admin
        context['users'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['primary_title'] = 'Members of Company: ' + company.name
        context['company'] = company
        return context

    def test_func(self):
        if self.request.user.is_staff:
            return True

        company = self.get_object()
        company_member = CompanyMembers.objects.filter(
            user_id=self.request.user.id, company_id=company.id)

        if company_member:
            return True
        return False

#  Working with/Reworking ideas from Google's AI / Gemini on the checklist selection perservation problem


@method_decorator(ratelimit(key='ip', rate='10/m', block=True), name='post')
class CompanyMemberListUpdateView(LoginAndValidationRequiredMixin, UpdateView):
    model = Company
    template_name = 'edit_members.html'
    form_class = CompanyForm

    def get_context_data(self,  **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.get_object()

        if self.request.GET.get('wipe_out'):
            self.request.session['selected_ids'] = None

        if self.request.session.get('selected_ids'):
            # pull the existing selected members in the checkbox list
            selected_values = self.request.session.get('selected_ids')
            selected_ids = [UUID(value) for value in selected_values]

        else:
            # Get the initial list of selected members from the CompanyMembers table
            member_uids = CompanyMembers.objects.filter(
                company_id=company.id).values_list('user_id', flat=True)
            member_uid_list = list(member_uids)
            selected_ids = member_uid_list

        # Either way, add any new members the user has selected and
        # remove any member selections the user has unchecked - on this particular page
        # - from the list of available user ids
        if self.request.GET.get('selected_users'):
            checked_values = json.loads(
                self.request.GET.get('selected_users'))
            checked_uuid_list = [UUID(value) for value in checked_values]
            selected_ids = list(
                set(selected_ids).union(set(checked_uuid_list)))

        if self.request.GET.get('unselected_users'):
            unchecked_values = json.loads(
                self.request.GET.get('unselected_users'))
            unchecked_uuid_list = [UUID(value) for value in unchecked_values]

            selected_ids = list(set(selected_ids) ^ set(unchecked_uuid_list))

        # test code for session items

        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(User.objects.all().order_by(
            'name'), 10)  # 10 users per page
        page_obj = paginator.get_page(page_number)

        context['users'] = page_obj.object_list
        context['company'] = company
        context['page_obj'] = page_obj
        context['selected_ids'] = selected_ids
        context['change_page_function'] = "navigateToPage"
        string_serialize_ids = [str(uuid) for uuid in selected_ids]

        self.request.session['selected_ids'] = string_serialize_ids

        return context

    def post(self, request, *args, **kwargs):
        company = self.get_object()

        selected_ids = self.request.session.get('selected_ids')
        selected_uuids = [UUID(value) for value in selected_ids]

        # only checked user ids on the current page
        checkbox_values = request.POST.getlist("member-checkbox")
        checked_uuid_list = [UUID(value) for value in checkbox_values]
        # all options on the current page.
        user_options = request.POST.getlist("member-checkbox-option")
        user_options_uuid_list = [UUID(value) for value in user_options]

        unchecked_uuid_set = set(
            user_options_uuid_list) - set(checked_uuid_list)

        selected_ids = list(set(selected_uuids).union(
            set(checked_uuid_list)) - unchecked_uuid_set)

        # delete every member who is in this company and NOT currently checked
        delete_member_uids = CompanyMembers.objects.filter(
            company_id=company.id).exclude(user_id__in=selected_ids).values_list('id', flat=True)
        delete_member_uids_list = list(delete_member_uids)

        CompanyMembers.objects.filter(id__in=delete_member_uids_list).delete()

        # Add every checked User to the CompanyMember db table - where
        # there isn't an entry for this user in this company already.
        for value in selected_ids:
            user = get_object_or_404(User, id=value)
            company_member = CompanyMembers.objects.get_or_create(
                company_id=company.id, user_id=user.id)

        # Clear away selected ids session variable.  It will be re-populated from the
        # CompanyMember table the next time the user wants to edit the Member list.
        self.request.session['selected_ids'] = None
        return redirect('display_company_members', pk=company.id)


class CompanyDeleteView(LoginAndValidationRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Company

    def post(self, request, *args, **kwargs):
        del_company = self.get_object()
        delete_company(del_company)
        return redirect('companies_list')

    def test_func(self):
        return self.request.user.is_staff


# Since this method has operations that must succeed or fail together,
# Putting a transaction at the top of this method.
def delete_company(del_company):
    with transaction.atomic():

        # First,  try to delete all the Company members
        # If any deletion fails down the chain,  the whole deletion
        # process should be canceled.
        delete_member_ids = CompanyMembers.objects.filter(
            company_id=del_company.id)
        for member in delete_member_ids:
            member.delete()

        del_company.delete()
        return "success"
