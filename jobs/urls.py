from django.urls import path
from .views import JobListView, JobDetailView, JobCreateView, JobUpdateView, JobDeleteView

app_name = 'jobs'

urlpatterns = [
    path('jobs/', JobListView.as_view(), name='job_list'),
    path('jobs/<uuid:job_id>/', JobDetailView.as_view(), name='job'),
    path('jobs/create/', JobCreateView.as_view(), name='create_job'),
    path('jobs/<uuid:job_id>/edit/', JobUpdateView.as_view(), name='edit_job'),
    path('jobs/<uuid:job_id>/delete/', JobDeleteView.as_view(), name='delete_job'),
]
