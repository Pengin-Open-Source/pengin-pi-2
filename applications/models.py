from django.db import models
from django.utils import timezone
from django.conf import settings  # Import settings module
from jobs.models import Job  # Import Job model from your project structure
import uuid

class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    resume = models.FileField(upload_to='resumes/')
    cover_letter = models.FileField(upload_to='cover_letters/', null=True, blank=True)
    message = models.TextField()
    location = models.CharField(max_length=100)
    date_applied = models.DateTimeField(default=timezone.now)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    status_code = models.ForeignKey('StatusCode', on_delete=models.CASCADE)
    status_code_date_change = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Application {self.id} for {self.job.job_title}"

class StatusCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.code
