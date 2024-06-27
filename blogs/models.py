from django.db import models, transaction
import uuid
from datetime import datetime
from django.utils import timezone
from main.models.users import User


class BlogPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100, unique=True)
    # EITHER editor (if one exists) or the author.
    # For now, if the user is deleted,  there will be a cascade delete of the blogposts,
    # BUT I intend to pre-emptdelete behavior,  and create a backup entry in the history table.
    # The plan is to leave deletion of history tables to the DBA
    user_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='blogposts')
    author = models.CharField(
        max_length=100, default='Error Getting Author - Should be User Name')
    edited_by = models.CharField(max_length=100, blank=True)
    date = models.DateTimeField(default=timezone.now)
    content = models.TextField(blank=True)
    tags = models.CharField(max_length=150,  blank=True)
    method = models.CharField(
        max_length=10, default='ERROR')
    roles = models.JSONField()

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            post_backup = BlogHistory(post_id=self.id, title=self.title, user=self.user_id,
                                      date=self.date, content=self.content, method=self.method, tags=self.tags, roles=self.roles)
            post_backup.save()

    def __str__(self):
        return str(self.title)


class BlogHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=100,  default='Error Getting Title')
    user = models.UUIDField(db_index=True)
    date = models.DateTimeField(default=timezone.now)
    content = models.TextField(blank=True)
    tags = models.CharField(max_length=150, blank=True)
    method = models.CharField(
        max_length=10, default='ERROR')
    roles = models.JSONField()
