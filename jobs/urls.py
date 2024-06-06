from django.urls import path
from .views import jobs, job

urlpatterns = [
    path('jobs', jobs, name='jobs'),
    path('jobs.html', jobs, name='jobs'),
    path('jobs/<int:job_id>/', job, name='job'),
]



