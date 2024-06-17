from django.db import models
import uuid
from datetime import datetime


class BlogPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100, unique=True)
    author = models.CharField(max_length=100)
    edited_by = models.CharField(max_length=100, unique=True)
    date = models.DateTimeField(default=datetime.utcnow)
    content = models.TextField()
    tags = models.CharField(max_length=150)
    method = models.CharField(max_length=10)

    def __str__(self):
        return str(self.title)


class Blogs_History(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=100)
    user = models.CharField(max_length=100)
    date = models.DateTimeField(default=datetime.utcnow)
    content = models.TextField()
    tags = models.CharField(max_length=150)
    method = models.CharField(max_length=10)
