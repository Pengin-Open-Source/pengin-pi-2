from django.db import models
import uuid
from datetime import datetime


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField()
    timestamp = models.CharField(max_length=100)
    # author must be linked in __init__.py
    # room must be linked in __init__.py


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    # members must be linked in __init__.py

    date_created = models.DateTimeField(default=datetime.now)


class UserRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
