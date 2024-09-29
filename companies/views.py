from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
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
                return redirect('display_company_info', company_id=member_company.company_id)
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


class CompanyDetailView(LoginAndValidationRequiredMixin, DetailView):
    model = Company
    template_name = 'company_info.html'
    context_object_name = 'company'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # company = get_object_or_404(Company, id=company_id)

        company = self.get_object()
        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        members = CompanyMembers.objects.filter(
            company_id=company.id).select_related('user')
        paginator = Paginator(members, 10)  # 10 members per page
        page_obj = paginator.get_page(page_number)
        is_admin = self.request.user.is_staff
        context['is_admin'] = is_admin
        context['primary_title'] = 'Company Info'
        context['company'] = company
        context['members'] = members
        return context


@login_required
def create_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.save()
            CompanyMembers.objects.create(company=company, user=request.user)
            print("Company created successfully:", company)
            return redirect('display_company_info', company_id=company.id)
        else:
            print("Form is not valid:", form.errors)
    else:
        form = CompanyForm()
    return render(request, 'company_info_create.html', {'form': form, 'primary_title': 'Create New Company'})


@login_required
def edit_company_info_post(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            return redirect('display_company_info', company_id=company.id)
    else:
        form = CompanyForm(instance=company)
    return render(request, 'company_edit.html', {
        'form': form,
        'company': company,
        'primary_title': 'Edit Company'
    })


@login_required
def display_company_members(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    page_number = request.POST.get(
        'page-number', 1) if request.method == "POST" else request.GET.get('page', 1)
    members_ids = CompanyMembers.objects.filter(
        company_id=company.id).values_list('user_id', flat=True)
    users = User.objects.filter(id__in=members_ids)
    paginator = Paginator(users, 10)  # 10 users per page
    page_obj = paginator.get_page(page_number)
    members_ids_list = list(members_ids)
    return render(request, 'display_members.html', {
        'users': page_obj.object_list,
        'company': company,
        'page_obj': page_obj,
        'members_ids_list': members_ids_list
    })


@login_required
def edit_company_members(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    page_number = request.POST.get(
        'page-number', 1) if request.method == "POST" else request.GET.get('page', 1)
    paginator = Paginator(User.objects.all(), 10)  # 10 users per page
    page_obj = paginator.get_page(page_number)
    member_uids = CompanyMembers.objects.filter(
        company_id=company.id).values_list('user_id', flat=True)
    member_uid_list = list(member_uids)
    return render(request, 'edit_members.html', {
        'users': page_obj.object_list,
        'company': company,
        'page_obj': page_obj,
        'member_uid_list': member_uid_list
    })


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
@login_required
def edit_company_members_post(request, company_id):
    if request.method == 'POST':
        company = get_object_or_404(Company, id=company_id)
        checkbox_values = request.POST.getlist('member-checkbox')
        # delete every member who is in this company and NOT currently checked
        delete_member_uids = CompanyMembers.objects.filter(
            company_id=company.id).exclude(user_id__in=checkbox_values).values_list('id', flat=True)
        delete_member_uids_list = list(delete_member_uids)
        CompanyMembers.objects.filter(id__in=delete_member_uids_list).delete()
        for value in checkbox_values:
            user = get_object_or_404(User, id=value)
            company_member = CompanyMembers.objects.get_or_create(
                company_id=company.id, user_id=user.id)
        return redirect('display_company_members', company_id=company.id)
