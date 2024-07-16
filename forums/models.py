from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group
from main.models.users import User
from django.utils import timezone
import uuid


class Thread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    date = models.DateTimeField(default=timezone.now)
    groups = models.ManyToManyField(
        Group, through='ThreadRole', related_name='threads')

    def __str__(self):
        return str(self.name)


class ForumPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=50)
    content = models.TextField()
    tags = models.CharField(max_length=150)
    date = models.DateTimeField(auto_now_add=True)
    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='posts')

    def __str__(self):
        return str(self.title)


class ForumComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(
        ForumPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments')
    # CREATE, EDIT, DELETE - which put the row in this state?
    # (DELETE is used for Comment History)
    row_action = models.CharField(max_length=10, default='ERROR')

    def __str__(self):
        return str(self.content)[:20]


class ForumCommentHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment_id = models.UUIDField(db_index=True)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    post = models.UUIDField(db_index=True)
    author = models.UUIDField(db_index=True)
    row_action = models.CharField(max_length=10, default='ERROR')


class ThreadRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
