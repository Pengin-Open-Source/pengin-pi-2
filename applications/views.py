from decouple import config
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from .forms import ApplicationForm
from .models import Application, Job, StatusCode
from util.security.auth_tools import is_admin_provider, is_admin_required
from util.s3 import File
from botocore.exceptions import ClientError

conn = File()


class ApplicationDetailView(LoginRequiredMixin, View):

    @method_decorator(is_admin_provider)
    def get(self, request, job_id, application_id, is_admin, *args, **kwargs):
        job = get_object_or_404(Job, id=job_id)
        application = get_object_or_404(Application, id=application_id)
        resume_url = application.resume.url if application.resume else ''
        cover_letter_url = application.cover_letter.url if application.cover_letter else ''
        context = {
            'job': job,
            'is_admin': is_admin,
            'application': application,
            'resume_url': resume_url,
            'cover_letter_url': cover_letter_url,
        }
        return render(request, 'application_view.html', context)


class CreateApplicationView(LoginRequiredMixin, View):

    def get(self, request, job_id):
        job = get_object_or_404(Job, id=job_id)
        form = ApplicationForm()
        return render(request, 'create_application.html', {'form': form, 'job': job})

    def post(self, request, job_id):
        job = get_object_or_404(Job, id=job_id)
        form = ApplicationForm(request.POST, request.FILES)

        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.user = request.user  # Assign current user to the application
            
            # Handle resume upload to S3
            resume = request.FILES.get('resume')
            if resume:
                try:
                    resume.filename = resume.name  # Ensure filename is set
                    application.resume = conn.create(resume)  # Upload to S3 and get URL
                except ClientError as e:
                    messages.error(request, f"Failed to upload resume: {e}")
                    return render(request, 'create_application.html', {'form': form, 'job': job})

            # Handle cover letter upload to S3
            cover_letter = request.FILES.get('cover_letter')
            if cover_letter:
                try:
                    cover_letter.filename = cover_letter.name  # Ensure filename is set
                    application.cover_letter = conn.create(cover_letter)  # Upload to S3 and get URL
                except ClientError as e:
                    messages.error(request, f"Failed to upload cover letter: {e}")
                    return render(request, 'create_application.html', {'form': form, 'job': job})

            # Retrieve or create 'pending' status code
            pending, created = StatusCode.objects.get_or_create(code='pending')
            application.status_code = pending  # Assign status code

            # Save the application
            application.save()

            # Provide success feedback to the user
            messages.success(request, 'Application submitted successfully!')
            return redirect('applications:application_success', job_id=job.id, application_id=application.id)
        else:
            # Provide feedback if the form is invalid
            messages.error(request, 'There was an error with your application. Please correct the highlighted fields.')
            return render(request, 'create_application.html', {'form': form, 'job': job})


class ApplicationSuccessView(View):

    def get(self, request, job_id, application_id):
        # Ensure context includes job_id and application_id correctly
        context = {
            'job_id': job_id,
            'application_id': application_id,
        }
        return render(request, 'application_success.html', context)


class MyApplicationsView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        applications_per_page = 9
        page_number = request.GET.get('page', 1)
        user_applications = Application.objects.filter(user=request.user).order_by('-date_applied')

        paginator = Paginator(user_applications, applications_per_page)
        page_obj = paginator.get_page(page_number)

        context = {
            'applications': page_obj,
            'page': page_obj.number,
            'primary_title': 'My Applications'
        }

        return render(request, 'my_applications.html', context)


class JobApplicationsView(LoginRequiredMixin, View):

    @method_decorator(is_admin_required)
    def get(self, request, job_id, *args, **kwargs):
        job = get_object_or_404(Job, id=job_id)
        status = request.GET.get('status')
        status_codes = StatusCode.objects.all()

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


class EditStatusView(LoginRequiredMixin, View):

    @method_decorator(is_admin_required)
    def get(self, request, job_id, application_id, *args, **kwargs):
        job = get_object_or_404(Job, id=job_id)
        application = get_object_or_404(Application, id=application_id)
        return render(request, 'edit_application.html', {'job': job, 'application': application, 'primary_title': 'Edit Application'})

    @method_decorator(is_admin_required)
    def post(self, request, job_id, application_id, *args, **kwargs):
        application = get_object_or_404(Application, id=application_id)
        form_status_code = request.POST.get('status_code')
        new_status_code, created = StatusCode.objects.get_or_create(code=form_status_code)

        application.status_code = new_status_code
        application.save()

        # Corrected the redirect to include the namespace
        return redirect('applications:job_applications', job_id=job_id)


class AcceptApplicantView(LoginRequiredMixin, View):

    @method_decorator(is_admin_required)
    def post(self, request, job_id, application_id, *args, **kwargs):
        application = get_object_or_404(Application, id=application_id)

        accept_subject = request.POST.get('accept-subject')
        accept_body = request.POST.get('accept-body')

        try:
            send_mail(
                accept_subject,
                accept_body,
                config('SES_SENDER'),
                [application.user.email],
                fail_silently=False,
            )
            new_status_code, created = StatusCode.objects.get_or_create(code='accepted')
            application.status_code = new_status_code
            application.save()
        except Exception as e:
            print('Error: ', e)

        # Redirect to job applications instead of application detail
        return redirect('applications:job_applications', job_id=job_id)


class RejectApplicantView(LoginRequiredMixin, View):

    @method_decorator(is_admin_required)
    def post(self, request, job_id, application_id, *args, **kwargs):
        application = get_object_or_404(Application, id=application_id)

        reject_subject = request.POST.get('reject-subject')
        reject_body = request.POST.get('reject-body')

        try:
            send_mail(
                reject_subject,
                reject_body,
                config('SES_SENDER'),
                [application.user.email],
                fail_silently=False,
            )
            new_status_code, created = StatusCode.objects.get_or_create(code='rejected')
            application.status_code = new_status_code
            application.save()
        except Exception as e:
            print('Error: ', e)

        # Redirect to job applications instead of application detail
        return redirect('applications:job_applications', job_id=job_id)


class DeleteApplicantView(LoginRequiredMixin, View):

    @method_decorator(is_admin_required)
    def post(self, request, job_id, application_id, *args, **kwargs):
        application = get_object_or_404(Application, id=application_id)
        status_code_id = request.POST.get('status_code_uuid')

        try:
            status_code = StatusCode.objects.get(id=status_code_id)
        except StatusCode.DoesNotExist:
            return HttpResponseNotFound("StatusCode not found")

        application.status_code = status_code
        application.save()
        application.delete()

        # Corrected redirect with the appropriate namespace
        return redirect('applications:job_applications', job_id=job_id)
