from django.urls import path
from .views import jobs, job, create_job, edit_job, delete_job

urlpatterns = [
    path('jobs', jobs, name='jobs'),
    path('jobs.html', jobs, name='jobs'),
    path('jobs/<int:job_id>/', job, name='job'),
    path('jobs/create/', create_job, name='create_job'),
    path('jobs/<uuid:job_id>/edit/', edit_job, name='edit_job'),
    path('jobs/<uuid:job_id>/delete/', delete_job, name='delete_job'),
]



