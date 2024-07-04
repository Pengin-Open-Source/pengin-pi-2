from django.shortcuts import render, redirect, get_object_or_404
from .models import Application, StatusCode
from .forms import ApplicationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def application_detail(request, job_id, application_id):
    application = get_object_or_404(Application, pk=application_id, job_id=job_id)
    resume_url = application.resume.url
    cover_letter_url = application.cover_letter.url if application.cover_letter else None
    return render(request, 'application_view.html', {'application': application, 'resume_url': resume_url, 'cover_letter_url': cover_letter_url})

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
