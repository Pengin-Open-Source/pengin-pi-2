# views.py
from django.http import HttpRequest
from .models import Job
from util.paginate import paginate  # Assuming you have a pagination utility
# Define the blog post view
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from util.security.auth_tools import is_admin_provider
from .forms import JobForm
from datetime import datetime


# Define the jobs view
@is_admin_provider
def jobs(request: HttpRequest, is_admin):
    jobs_per_page = 9
    if request.method == 'POST':
        page = int(request.POST.get('page_number', 1))
    else:
        page = 1

    jobs_paginated = paginate(Job.objects.all, page=page, key='priority', per_page=jobs_per_page)
    
    return render(request, 'jobs.html', {
        'is_admin': is_admin,
        'jobs': jobs_paginated,
        'page': page,
        'primary_title': 'Jobs',
    })

# Define the job view
@is_admin_provider
def job(request: HttpRequest, job_id: int, is_admin):
    job = get_object_or_404(Job, id=job_id)

    applications = job.applications.all()
    user_applied = applications.filter(user_id=request.user.id).exists()
    user_application_id = applications.filter(user_id=request.user.id).values_list('id', flat=True).first()
    
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
@permission_required('yourapp.add_job', raise_exception=True)
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
    return render(request, 'jobs/job_create.html', context)

@login_required
@permission_required('yourapp.change_job', raise_exception=True)
def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect('job_detail', job_id=job.id)  # Redirect to job detail view after edit
    else:
        form = JobForm(instance=job)

    context = {
        'form': form,
        'job': job,
        'primary_title': 'Edit Job',
    }
    return render(request, 'jobs/job_edit.html', context)

@login_required
@permission_required('yourapp.delete_job', raise_exception=True)
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    
    if request.method == 'POST':
        job.delete()
        return redirect('job_list')  # Redirect to job list view after deletion

    context = {
        'job': job,
    }
    return render(request, 'jobs/job_confirm_delete.html', context)
