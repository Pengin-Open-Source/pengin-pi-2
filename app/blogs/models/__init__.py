from django.db import models
from datetime import datetime
from django.utils import timezone


class BlogPost(models.Model):
    # __tablename__ = "blogpost"
    id = models.CharField(max_length=36,  default=id,  primary_key=True)
    title = models.CharField(max_length=100, unique=True)
    date = models.DateTimeField(default=timezone.now)
    content = models.TextField()
    tags = models.CharField(max_length=150)
