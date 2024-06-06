from django.db import models
import uuid
from datetime import datetime


class BlogPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100, unique=True)
    date = models.DateTimeField(default=datetime.utcnow)
    content = models.TextField()
    tags = models.CharField(max_length=150)

    def __str__(self):
        return self.title