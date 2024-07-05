from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Company, CompanyMembers
from main.models.users import User  
from .forms import CompanyForm
from django_ratelimit.decorators import ratelimit

@login_required
def display_companies_home(request):
    if request.user.has_perm('admin_permission'):
        return handle_admin_view(request)
    else:
        return handle_user_view(request)

def handle_admin_view(request):
    page_number = request.POST.get('page_number', 1) if request.method == "POST" else request.GET.get('page', 1)
    companies = Company.objects.all()
    paginator = Paginator(companies, 10)  # 10 companies per page
    page_obj = paginator.get_page(page_number)
    return render(request, 'company_info_main.html', {
        'companies': page_obj, 'is_admin': True, 'primary_title': 'Companies'
    })

def handle_user_view(request):
    member_company = CompanyMembers.objects.filter(user_id=request.user.id).first()
    if member_company:
        return redirect('display_company_info', company_id=member_company.company_id)
    return render(request, 'no_company.html')

@login_required
def display_company_info(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    page_number = request.POST.get('page-number', 1) if request.method == "POST" else request.GET.get('page', 1)
    members = CompanyMembers.objects.filter(company_id=company_id).select_related('user')
    paginator = Paginator(members, 10)  # 10 members per page
    page_obj = paginator.get_page(page_number)
    is_admin = request.user.has_perm('admin')
    return render(request, 'company_info.html', {
        'primary_title': 'Company Info',
        'company': company,
        'members': page_obj,
        'is_admin': is_admin
    })

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
    page_number = request.POST.get('page-number', 1) if request.method == "POST" else request.GET.get('page', 1)
    members_ids = CompanyMembers.objects.filter(company_id=company.id).values_list('user_id', flat=True)
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
    page_number = request.POST.get('page-number', 1) if request.method == "POST" else request.GET.get('page', 1)
    paginator = Paginator(User.objects.all(), 10)  # 10 users per page
    page_obj = paginator.get_page(page_number)
    members_ids = CompanyMembers.objects.filter(company_id=company.id).values_list('user_id', flat=True)
    members_ids_list = list(members_ids)
    return render(request, 'edit_members.html', {
        'users': page_obj.object_list,
        'company': company,
        'page_obj': page_obj,
        'members_ids_list': members_ids_list
    })

@ratelimit(key='ip', rate='10/m', method='POST', block=True)  
@login_required
def edit_company_members_post(request, company_id):
    if request.method == 'POST':
        company = get_object_or_404(Company, id=company_id)
        checkbox_values = request.POST.getlist('member-checkbox')
        page_number = request.POST.get('page-number')
        users_for_delete = Paginator(User.objects.all(), 10).page(int(page_number))
        members_ids = CompanyMembers.objects.filter(company_id=company.id).values_list('user_id', flat=True)
        members_ids_list = list(members_ids)
        CompanyMembers.objects.filter(user_id__in=users_for_delete).delete()
        for value in checkbox_values:
            user = get_object_or_404(User, id=value)
            new_member = CompanyMembers.objects.create(company_id=company.id, user_id=user.id)
        return redirect('display_company_members', company_id=company.id)
