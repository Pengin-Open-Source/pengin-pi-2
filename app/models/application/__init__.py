from django.db import models
import uuid
from datetime import datetime


class StatusCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True, nullable=False)

    def __str__(self):
        return str(self.code)


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume_path = models.CharField(max_length=100)
    cover_letter_path = models.CharField(max_length=100)
    message = models.TextField()
    location = models.CharField(max_length=100)
    date_applied = models.DateTimeField(null=True, blank=True)
    status_code = models.ForeignKey(StatusCode, on_delete=models.CASCADE)
    status_code_date_change = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Application {self.id} - {self.status_code}"
