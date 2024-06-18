from django.db import models, transaction
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

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.method == 'CREATE':
                poster = self.author
            elif self.method == 'EDIT':
                poster = self.edited_by
            post_backup = BlogHistory(post_id=self.id, title=self.title, user=poster,
                                      date=self.date, content=self.content, method=self.method, tags=self.tags)
            post_backup.save()

    def __str__(self):
        return str(self.title)


class BlogHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=100)
    user = models.CharField(max_length=100)
    date = models.DateTimeField(default=datetime.utcnow)
    content = models.TextField()
    tags = models.CharField(max_length=150)
    method = models.CharField(max_length=10)
