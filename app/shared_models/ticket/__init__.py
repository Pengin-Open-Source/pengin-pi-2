from django.db import models
import uuid
from django.utils import timezone


class TicketForum(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4())
    summary = models.CharField(max_length=100)
    content = models.TextField()
    tags = models.CharField(max_length=150)
    date = models.CharField(max_length=100)
    resolution_status = models.CharField(max_length=100)
    resolution_date = models.CharField(max_length=100)


class Resolution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4())
    name = models.CharField(max_length=100)
    date = models.DateTimeField(default=timezone.now)


class TicketComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4())
    date = models.CharField(max_length=100)
    content = models.TextField()
