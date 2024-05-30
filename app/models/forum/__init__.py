# forum/models.py

from django.db import models
import uuid

class ForumPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=50)
    content = models.TextField()
    tags = models.CharField(max_length=150)
    date = models.CharField(max_length=100)

    def __str__(self):
        return self.title


class ForumComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField()
    date = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=100)

    def __str__(self):
        return f"Comment {self.id}"


class Thread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ThreadRoles(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return f"ThreadRole {self.id}"
