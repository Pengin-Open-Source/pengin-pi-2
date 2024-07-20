from decouple import config
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .forms import ApplicationForm
from .models import Application, Job, StatusCode
from util.security.auth_tools import is_admin_provider, is_admin_required

def application_detail(request, job_id, application_id):
    job = get_object_or_404(Job, id=job_id)
    application = get_object_or_404(Application, id=application_id)
    resume_url = application.resume.url if application.resume else ''
    cover_letter_url = application.cover_letter.url if application.cover_letter else ''
    context = {
        'job': job,
        'application': application,
        'resume_url': resume_url,
        'cover_letter_url': cover_letter_url,
    }
    return render(request, 'application_view.html', context)

@login_required
def create_application(request, job_id):
    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job_id = job_id
            application.user = request.user  # Assign current user to the application

            # Retrieve or create 'pending' status code
            pending, created = StatusCode.objects.get_or_create(code='pending')
            application.status_code = pending  # Assign status code

            application.save()

            messages.success(request, 'Application submitted successfully!')
            return redirect('application_success', job_id=job_id, application_id=application.id)
    else:
        form = ApplicationForm()

    return render(request, 'create_application.html', {'form': form, 'job_id': job_id})

@login_required
def application_success(request, job_id, application_id):
    return render(request, 'application_success.html', {'job_id': job_id, 'application_id': application_id})

@login_required
def my_applications(request):
    applications_per_page = 9
    page_number = request.GET.get('page', 1)
    user_applications = Application.objects.filter(user_id=request.user.id).order_by('-date_applied')
    
    paginator = Paginator(user_applications, applications_per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'applications': page_obj,
        'page': page_obj.number,
        'primary_title': 'My Applications'
    }

    return render(request, 'my_applications.html', context)

@login_required
@is_admin_required
def job_applications(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    status = request.GET.get('status')
    status_codes = StatusCode.objects.all()

    if request.method == "POST":
        page = int(request.POST.get('page_number', 1))
    else:
        page = int(request.GET.get('page', 1))

    if status:
        applications = Application.objects.filter(
            status_code__code=status,
            job=job
        )
    else:
        applications = Application.objects.filter(
            ~Q(status_code__code='deleted'),
            job=job
        )

    paginator = Paginator(applications, 10)
    paginated_applications = paginator.get_page(page)

    return render(request, 'job_applications.html', {
        'job': job,
        'applications': paginated_applications,
        'status_codes': status_codes,
        'primary_title': 'Job Applications',
        'status': status,
        'page_obj': paginated_applications,
    })

@login_required
@is_admin_required
def edit_status(request, job_id, application_id):
    job = get_object_or_404(Job, id=job_id)
    application = get_object_or_404(Application, id=application_id)
    
    if request.method == 'POST':
        form_status_code = request.POST.get('status_code')
        new_status_code, created = StatusCode.objects.get_or_create(code=form_status_code)

        application.status_code = new_status_code
        application.save()

        return redirect('job_applications', job_id=job_id)

    return render(request, 'edit_application.html', {'job': job, 'application': application, 'primary_title': 'Edit Application'})

@login_required
@is_admin_required
def accept_applicant(request, job_id, application_id):
    # Retrieve the application object
    application = get_object_or_404(Application, id=application_id)

    # Retrieve accept subject and body from POST data
    accept_subject = request.POST.get('accept-subject')
    accept_body = request.POST.get('accept-body')

    try:
        # Send acceptance email
        send_mail(
                accept_subject,
                accept_body,
                config('SES_SENDER'),  # Use environment variable
                [application.user.email],
                fail_silently=False,
            )
        # Check if 'accepted' status code exists in the database; if not, create it
        new_status_code, created = StatusCode.objects.get_or_create(code='accepted')

        # Update application status to 'accepted'
        application.status_code = new_status_code
        application.save()

    except Exception as e:
        print('Error: ', e)
        # Handle the error gracefully, perhaps log it

    # Redirect back to application view
    return redirect('application_detail', job_id=job_id, application_id=application_id)

@login_required
@is_admin_required
def reject_applicant(request, job_id, application_id):
    # Retrieve the application object
    application = get_object_or_404(Application, id=application_id)

    # Retrieve reject subject and body from POST data
    reject_subject = request.POST.get('reject-subject')
    reject_body = request.POST.get('reject-body')

    try:
        # Send rejection email
        send_mail(
                reject_subject,
                reject_body,
                config('SES_SENDER'),  # Use environment variable
                [application.user.email],
                fail_silently=False,
            )
        
        # Check if 'rejected' status code exists in the database; if not, create it
        new_status_code, created = StatusCode.objects.get_or_create(code='rejected')

        # Update application status to 'rejected'
        application.status_code = new_status_code
        application.save()

    except Exception as e:
        print('Error: ', e)
        # Handle the error gracefully, perhaps log it

    # Redirect back to application view
    return redirect('application_detail', job_id=job_id, application_id=application_id)

@login_required
@is_admin_required
def delete_applicant(request, job_id, application_id):
    application = get_object_or_404(Application, id=application_id)

    try:
        # check whether 'deleted' code exists in db; if not, create it
        new_status_code, created = StatusCode.objects.get_or_create(code='deleted')

        application.status_code = new_status_code.id
        application.save()

    except Exception as e:
        print('Error: ', e)

    return redirect(reverse('applications:job_applications', args=[job_id]))