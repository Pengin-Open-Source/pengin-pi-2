from django.http import HttpRequest
from models import Job
from util import paginate  # Assuming you have a pagination utility
# Define the blog post view
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test


# Define the jobs view
def jobs(request: HttpRequest):
    jobs_per_page = 9
    if request.method == 'POST':
        page = int(request.POST.get('page_number', 1))
    else:
        page = 1

    jobs_paginated = paginate(Job, page=page, key='job_title', pages=jobs_per_page)
    is_admin = user_passes_test(lambda u: u.is_staff)(request.user)
    
    return render(request, 'jobs.html', {
        'is_admin': is_admin,
        'jobs': jobs_paginated,
        'page': page,
        'primary_title': 'Jobs',
    })

# Define the job view
def job(request: HttpRequest, job_id: int):
    job = get_object_or_404(Job, id=job_id)

    applications = job.applications.all()
    user_applied = applications.filter(user_id=request.user.id).exists()
    user_application_id = applications.filter(user_id=request.user.id).values_list('id', flat=True).first()
    is_admin = user_passes_test(lambda u: u.is_staff)(request.user)
    
    return render(request, 'job.html', {
        'is_admin': is_admin,
        'job': job,
        'applications': applications,
        'user_applied': user_applied,
        'user_application_id': user_application_id,
        'page': 1,
        'primary_title': job.job_title,
    })