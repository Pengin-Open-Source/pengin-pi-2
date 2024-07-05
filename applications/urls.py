from django.urls import path
from . import views

urlpatterns = [
    path('<uuid:job_id>/application/<uuid:application_id>', views.application_detail, name='application_detail'),
    path('<uuid:job_id>/application/create', views.create_application, name='create_application'),
    path('<uuid:job_id>/application/<uuid:application_id>/success', views.application_success, name='application_success'),
    #path('<uuid:job_id>/<uuid:application_id>/edit-status', views.edit_status, name='edit_status'),
    #path('<uuid:job_id>/<uuid:application_id>/accept', views.accept_applicant, name='accept_applicant'),
    #path('<uuid:job_id>/<uuid:application_id>/reject', views.reject_applicant, name='reject_applicant'),
    #path('<uuid:job_id>/<uuid:application_id>/delete', views.delete_applicant, name='delete_applicant'),
    #path('my-applications', views.my_applications, name='my_applications'),
    path('<uuid:job_id>/job-applications', views.job_applications, name='job_applications'),
]
