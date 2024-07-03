from django.urls import path
from .views import jobs, job, create_job, edit_job, delete_job

urlpatterns = [
    path('jobs/', jobs, name='job_list'),  # Redirect /jobs/ to the jobs view
    path('jobs/<uuid:job_id>/', job, name='job'),  # View job details
    path('jobs/create/', create_job, name='create_job'),  # Create a new job
    path('jobs/<uuid:job_id>/edit/', edit_job, name='edit_job'),  # Edit job details
    path('jobs/<uuid:job_id>/delete/', delete_job, name='delete_job'),  # Delete job confirmation
]
