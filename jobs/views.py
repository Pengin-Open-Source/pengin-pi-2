from django.http import HttpRequest
from .models import Job
from util.paginate import paginate  # Assuming you have a pagination utility
# Define the blog post view
from django.shortcuts import render, get_object_or_404
from util.security.auth_tools import is_admin_provider

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