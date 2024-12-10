# applications/urls.py
from django.urls import path
from .views import (
    ApplicationDetailView,
    CreateApplicationView,
    ApplicationSuccessView,
    MyApplicationsView,
    JobApplicationsView,
    EditStatusView,
    AcceptApplicantView,
    RejectApplicantView,
    DeleteApplicantView,
)

app_name = 'applications'

urlpatterns = [
    path('applications/<uuid:job_id>/application/<uuid:application_id>/', ApplicationDetailView.as_view(), name='application_detail'),
    path('applications/<uuid:job_id>/application/create/', CreateApplicationView.as_view(), name='create_application'),
    path('applications/<uuid:job_id>/application/<uuid:application_id>/success/', ApplicationSuccessView.as_view(), name='application_success'),
    path('applications/<uuid:job_id>/application/<uuid:application_id>/edit-status/', EditStatusView.as_view(), name='edit_status'),
    path('applications/<uuid:job_id>/application/<uuid:application_id>/accept/', AcceptApplicantView.as_view(), name='accept_applicant'),
    path('applications/<uuid:job_id>/application/<uuid:application_id>/reject/', RejectApplicantView.as_view(), name='reject_applicant'),
    path('applications/<uuid:job_id>/application/<uuid:application_id>/delete/', DeleteApplicantView.as_view(), name='delete_applicant'),
    path('my_applications/', MyApplicationsView.as_view(), name='my_applications'),
    path('applications/<uuid:job_id>/job-applications/', JobApplicationsView.as_view(), name='job_applications'),
]
