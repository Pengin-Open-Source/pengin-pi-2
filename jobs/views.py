import uuid
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from .forms import JobForm
from .models import Job
from util.security.auth_tools import group_required, is_admin_provider

# Set view permissions based off of group
#???_required = group_required('???')

@is_admin_provider
def jobs(request: HttpRequest, is_admin):

    page = int(request.GET.get('page', 1))

    jobs = Job.objects.all().order_by('priority', '-date_posted')
    paginator = Paginator(jobs, 10)
    jobs_paginated = paginator.get_page(page)
    
    # Accessing the current authenticated user
    current_user = request.user

    # Print current user info to the command line
    print(f"Current user: {current_user.username} (ID: {current_user.id})")

    return render(request, 'jobs.html', {
        'is_admin': is_admin,
        'jobs': jobs_paginated,
        'page_obj': jobs_paginated, 
    })

@is_admin_provider
def job(request: HttpRequest, job_id: uuid.UUID, is_admin):  # Change to UUID here
    job = get_object_or_404(Job, id=job_id)

    applications = job.applications.all()
    user_applied = applications.filter(user=request.user).exists()  # Use 'user' instead of 'user_id'
    user_application_id = applications.filter(user=request.user).values_list('id', flat=True).first()  # Use 'user' instead of 'user_id'
    
    return render(request, 'job.html', {
        'is_admin': is_admin,
        'job': job,
        'applications': applications,
        'user_applied': user_applied,
        'user_application_id': user_application_id,
        'page': 1,
        'primary_title': job.job_title,
    })

@login_required
def create_job(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.date_posted = datetime.now()
            job.save()
            return redirect('job_list')  # Redirect to job list view after creation
    else:
        form = JobForm()

    context = {
        'form': form,
        'primary_title': 'Create Job',
    }
    return render(request, 'job_create.html', context)

@login_required
def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect('job', job_id=job.id)  # Redirect to job detail view after edit
    else:
        form = JobForm(instance=job)

    context = {
        'form': form,
        'job': job,
        'primary_title': 'Edit Job',
    }
    return render(request, 'job_edit.html', context)

@login_required
def delete_job(request: HttpRequest, job_id: uuid.UUID) -> HttpResponse:
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        if request.POST.get('confirm_delete'):
            job.delete()
            return redirect('job_list')  # Redirect to job list view after deletion
        else:
            # Handle case where confirmation checkbox is not checked
            return render(request, 'job_confirm_delete.html', {'job': job})
    
    context = {
        'job': job,
    }
    return render(request, 'job_confirm_delete.html', context)