from django.db import models
import uuid
from datetime import datetime


class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_title = models.CharField(max_length=100)
    short_description = models.CharField(max_length=280)
    long_description = models.TextField()
    department = models.CharField(max_length=100)
    salary = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    hiring_manager = models.CharField(max_length=100)
    date_posted = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.job_title)
