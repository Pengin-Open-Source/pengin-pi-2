import uuid
from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views import View
from .forms import JobForm
from .models import Job
from util.security.auth_tools import is_admin_provider, is_admin_required

class JobListView(View):
    
    @method_decorator(is_admin_provider)
    def get(self, request, is_admin, *args, **kwargs):
        page = int(request.GET.get('page', 1))
        jobs = Job.objects.all().order_by('priority', '-date_posted')
        paginator = Paginator(jobs, 10)
        jobs_paginated = paginator.get_page(page)

        context = {
            'is_admin': is_admin,
            'jobs': jobs_paginated,
            'page_obj': jobs_paginated,
        }
        return render(request, 'jobs.html', context)

class JobDetailView(View):

    @method_decorator(is_admin_provider)
    def get(self, request, is_admin, job_id, *args, **kwargs):
        job = get_object_or_404(Job, id=job_id)

        # Check if the user is authenticated before performing user-specific logic
        user_applied = False
        user_application_id = None
        if request.user.is_authenticated:
            # Only filter applications for logged-in users
            user_applications = job.applications.filter(user=request.user)
            user_applied = user_applications.exists()
            user_application_id = user_applications.values_list('id', flat=True).first()

        context = {
            'is_admin': is_admin,
            'job': job,
            'user_applied': user_applied,
            'user_application_id': user_application_id,
            'page': 1,
            'primary_title': job.job_title,
        }
        return render(request, 'job.html', context)

    def post(self, request, job_id, *args, **kwargs):
        if not request.user.is_authenticated:
            # Redirect to login if the user is not authenticated
            return redirect('login')

        job = get_object_or_404(Job, id=job_id)
        # Check if the user has already applied
        user_applied = job.applications.filter(user=request.user).exists()

        if user_applied:
            # Return a 403 Forbidden if the user has already applied
            return HttpResponseForbidden("You have already applied for this job.")

        # Additional logic for handling valid application scenario
        return redirect('applications:create_application', job_id=job.id)

class JobCreateView(LoginRequiredMixin, View):
    
    @method_decorator(is_admin_required)
    def get(self, request, *args, **kwargs):
        form = JobForm()
        context = {
            'form': form,
            'primary_title': 'Create Job',
        }
        return render(request, 'job_create.html', context)

    @method_decorator(is_admin_required)
    def post(self, request, *args, **kwargs):
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.date_posted = datetime.now()
            job.save()
            return redirect('job_list')  # Redirect to job list view after creation

        context = {
            'form': form,
            'primary_title': 'Create Job',
        }
        return render(request, 'job_create.html', context)

class JobUpdateView(LoginRequiredMixin, View):
    
    @method_decorator(is_admin_required)
    def get(self, request, job_id, *args, **kwargs):
        job = get_object_or_404(Job, id=job_id)
        form = JobForm(instance=job)
        context = {
            'form': form,
            'job': job,
            'primary_title': 'Edit Job',
        }
        return render(request, 'job_edit.html', context)

    @method_decorator(is_admin_required)
    def post(self, request, job_id, *args, **kwargs):
        job = get_object_or_404(Job, id=job_id)
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect('job', job_id=job.id)  # Redirect to job detail view after edit

        context = {
            'form': form,
            'job': job,
            'primary_title': 'Edit Job',
        }
        return render(request, 'job_edit.html', context)

class JobDeleteView(LoginRequiredMixin, View):
    
    @method_decorator(is_admin_required)
    def get(self, request, job_id, *args, **kwargs):
        job = get_object_or_404(Job, id=job_id)
        context = {
            'job': job,
        }
        return render(request, 'job_confirm_delete.html', context)

    @method_decorator(is_admin_required)
    def post(self, request, job_id, *args, **kwargs):
        job = get_object_or_404(Job, id=job_id)
        if 'confirm_delete' in request.POST:
            job.delete()
            return redirect('job_list')  # Redirect to job list view after deletion

        # Handle case where confirmation checkbox is not checked
        context = {
            'job': job,
        }
        return render(request, 'job_confirm_delete.html', context)
