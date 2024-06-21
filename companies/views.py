from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, admin_required
from django.core.paginator import Paginator
from .models import Company, CompanyMembers
from .forms import CompanyForm

@login_required
def display_companies_home(request):
    if request.user.has_perm('admin_permission'):
        return handle_admin_view(request)
    else:
        return handle_user_view(request)

def handle_admin_view(request):
    if request.method == "POST":
        page = int(request.POST.get('page_number', 1))
    else:
        page = 1
    companies = Company.objects.all()
    paginator = Paginator(companies, 10)  # 10 companies per page
    companies_page = paginator.get_page(page)
    return render(request, 'company_info/company_info_main.html', {
        'companies': companies_page, 'is_admin': True, 'primary_title': 'Companies'
    })

def handle_user_view(request):
    member_company = CompanyMembers.objects.filter(user_id=request.user.id).first()
    if member_company:
        return redirect('display_company_info', company_id=member_company.company_id)
    return render(request, 'company_info/no_company.html')


@login_required
@admin_required
def display_company_info(request, company_id):
    """display company info method
    This method handles the company/company_id route and returns a company information view.

    Required Inputs:
        company_id: company UUID4 string

    Outputs:
        render_template -> company_info.html
    Output Arguments:
        company_info.html, company query, paginated company members
    """

    # Get company from database
    company = get_object_or_404(Company, id=company_id)

    # If POST, get page number from form button
    page = request.POST.get('page_number', 1) if request.method == "POST" else 1

    # Custom paginate method to join two tables and paginate results. Gets users where members of company_id
    members = CompanyMembers.objects.filter(company_id=company_id).select_related('user')
    paginator = Paginator(members, 10)  # 10 members per page
    paginated_members = paginator.get_page(page)

    is_admin = request.user.has_perm('admin')

    return render(request, 'company_info/company_info.html', {
        'primary_title': 'Company Info',
        'company': company,
        'members': paginated_members,
        'is_admin': is_admin
    })


@login_required
@admin_required  # Ensure you have this custom decorator defined
def create_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.save()
            CompanyMembers.objects.create(company=company, user=request.user)
            return redirect('display_company_info', company_id=company.id)
    else:
        form = CompanyForm()

    return render(request, 'company_info/company_info_create.html', {'form': form, 'primary_title': 'Create New Company'})


@login_required
@admin_required  # Ensure you have this custom decorator defined
def edit_company_info_post(request, company_id):
    company = get_object_or_404(Company, id=company_id)

    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            return redirect('display_company_info', company_id=company.id)
    else:
        form = CompanyForm(instance=company)

    return render(request, 'company_info/company_edit.html', {'form': form, 'primary_title': 'Edit Company'})

@login_required
def display_company_members(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    
    page = int(request.POST.get('page_number', 1)) if request.method == "POST" else 1

    paginator = Paginator(User.objects.all(), 10)  # 10 users per page
    users = paginator.get_page(page)

    members_ids = CompanyMembers.objects.filter(company_id=company.id).values_list('user_id', flat=True)
    members_ids_list = list(members_ids)

    return render(request, 'company_info/display_members.html', {
        'users': users,
        'company': company,
        'page': page,
        'members_ids_list': members_ids_list
    })


@login_required
@admin_required  # Ensure you have this custom decorator defined
def edit_company_members(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    page = int(request.POST.get('page_number', 1)) if request.method == "POST" else 1

    paginator = Paginator(User.objects.all(), 10)  # 10 users per page
    users = paginator.get_page(page)

    members_ids = CompanyMembers.objects.filter(company_id=company.id).values_list('user_id', flat=True)
    members_ids_list = list(members_ids)

    return render(request, 'company_info/edit_members.html', {
        'users': users,
        'company': company,
        'page': page,
        'members_ids_list': members_ids_list
    })


@limiter.limit("10 per minute")  # Assuming you have implemented rate limiting in Django
@login_required
@admin_required  # Ensure you have this custom decorator defined
def edit_company_members_post(request, company_id):
    if request.method == 'POST':
        company = get_object_or_404(Company, id=company_id)
        checkbox_values = request.POST.getlist('member-checkbox')
        page_num = request.POST.get('page-number')
        users_for_delete = Paginator(User.objects.all(), 9).page(int(page_num))
        members_ids = CompanyMembers.objects.filter(company_id=company.id).values_list('user_id', flat=True)
        members_ids_list = list(members_ids)

        # Clear members so only those with checkboxes are left in DB.
        CompanyMembers.objects.filter(user_id__in=users_for_delete).delete()

        for value in checkbox_values:
            user = get_object_or_404(User, id=value)
            new_member = CompanyMembers.objects.create(company_id=company.id, user_id=user.id)

        return redirect('edit_company_members', company_id=company.id)