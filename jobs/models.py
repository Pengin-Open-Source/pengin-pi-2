from django.db import models
import uuid


class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_title = models.CharField(max_length=100)
    short_description = models.CharField(max_length=280)
    long_description = models.TextField()
    department = models.CharField(max_length=100)
    salary = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    hiring_manager = models.CharField(max_length=100)
    priority = models.IntegerField(default=10000)
    date_posted = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.job_title
    
    class Meta:
        permissions = [
            ("change_job", "Can change job"),
            ("add_job", "Can add job"),
            ("delete_job", "Can delete job"),
        ]