from django.db import models, transaction
import uuid
from datetime import datetime
from django.utils import timezone


class BlogPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100, unique=True)
    author = models.CharField(
        max_length=100, default='Error Getting Author - Should be User Name')
    edited_by = models.CharField(max_length=100, blank=True)
    date = models.DateTimeField(default=timezone.now)
    content = models.TextField(blank=True)
    tags = models.CharField(max_length=150,  blank=True)
    method = models.CharField(
        max_length=10, default='Error Getting Method Type- Should be CREATE OR EDIT')

    def save(self, *args, **kwargs):
        with transaction.atomic():
            poster = 'If you see this there was a problem'
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
    title = models.CharField(max_length=100,  default='Error Getting Title')
    user = models.CharField(
        max_length=100, default='Error Getting Author/Editor')
    date = models.DateTimeField(default=timezone.now)
    content = models.TextField(blank=True)
    tags = models.CharField(max_length=150, blank=True)
    method = models.CharField(
        max_length=10, default='Error Getting Method Type- Should be CREATE OR EDIT')
