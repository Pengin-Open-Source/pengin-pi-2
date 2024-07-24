from django.db import models
from django.db import models, transaction
from django.conf import settings
from django.contrib.auth.models import Group
from main.models.users import User
from django.utils import timezone
import uuid


class Thread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    date = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='threads')
    groups = models.ManyToManyField(
        Group, through='ThreadRole', related_name='threads')
    row_action = models.CharField(max_length=10, default='ERROR')

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        save_method = self.row_action
        # all backups must complete properly for changes to be saved
        with transaction.atomic():
            # Do backup of current values in the row first.
            # (Note we backup before a DELETE.  Frequently,  a
            # row will have no backup history until we enter DELETE)
            # Rows will still be backed up even if 'ERROR' was assigned to the row_action.
            if save_method != "CREATE":
                original_thread = Thread.objects.get(pk=self.pk)

                # KEY ASSUMPTION FOR THE FOLLOWING TO BE ACCURATE:
                # No one will change the groups-thread relationship, except by editing the thread
                # (IE,  adding or removing a role from a thread, on a Forum Thread "Edit" page)
                # Also note that while the pk of group associated with a thread should not change,
                # it is theorectically possible for the NAME of group to change since the time it was
                # Linked to this thread (hence we save both in history)

                thread_groups = original_thread.groups.all()
                groups_snapshot = list(thread_groups.values('pk', 'name'))
                thread_backup = ThreadHistory(thread_id=original_thread.pk, name=original_thread.name, date=original_thread.date,
                                              user=original_thread.user.pk, roles=groups_snapshot, row_action=original_thread.row_action)
                thread_backup.save()

            # else: this is a newly created Thread/Forum don't save it to backup table yet

            # In any event (but a rollback),  save this new Forum or Forum update to the database.
            super().save(*args, **kwargs)

            # if this is a pre-delete save,  the Thread row will have been updated to contain
            # 1) The action/method: "DELETE"
            # 2) The User who did the Delete
            # 3) The time of the deletion
            # We need to make sure this information is copied into Thread history
            # before we delete this Thread.
            # (If Thread history needs to be totally deleted, that should be done
            # by a DBA)
            if save_method == 'DELETE':
                # FYI, reusing groups_snapshot since it shouldn't have changed since the "last change" backup save
                archived_thread = ThreadHistory(thread_id=self.pk, name=self.name, date=self.date,
                                                user=self.user.pk, roles=groups_snapshot, row_action=self.row_action)
                archived_thread.save()


class ThreadHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=100)
    date = models.DateTimeField(default=timezone.now)
    user = models.UUIDField(db_index=True)
    roles = models.JSONField()
    row_action = models.CharField(max_length=10, default='ERROR')


class ForumPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=50)
    content = models.TextField()
    tags = models.CharField(max_length=150)
    date = models.DateTimeField(default=timezone.now)
    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='posts')
    row_action = models.CharField(max_length=10, default='ERROR')

    def __str__(self):
        return str(self.title)

    def save(self, *args, **kwargs):
        save_method = self.row_action
        # all backups must complete properly for changes to be saved
        with transaction.atomic():
            # Do backup of current values in the row first.
            # (Note we backup before a DELETE.  Frequently,  a
            # row will have no backup history until we enter DELETE)
            # Rows will still be backed up even if 'ERROR' was assigned to the row_action.
            if save_method != "CREATE":
                original_post = ForumPost.objects.get(pk=self.pk)
                post_backup = ForumPostHistory(post_id=original_post.id, title=original_post.title, content=original_post.content,  tags=original_post.tags, date=original_post.date, thread=original_post.thread.pk,
                                               author=original_post.author.pk, row_action=original_post.row_action)
                post_backup.save()

            # else: this is a newly created post don't save it to backup table yet

            # In any event (but a rollback),  save this new post or post update to the database.
            super().save(*args, **kwargs)

            # if this is a pre-delete save,  the post row will have been updated to contain
            # 1) The action/method: "DELETE"
            # 2) The User who did the Delete
            # 3) The time of the deletion
            # We need to make sure this information is copied into post history
            # before we delete the post.
            # (If post history needs to be totally deleted, that should be done
            # by a DBA)
            if save_method == 'DELETE':
                archived_post = ForumPostHistory(post_id=self.pk, title=self.title, content=self.content,  tags=self.tags, date=self.date, thread=self.thread.pk,
                                                 author=self.author.pk, row_action=self.row_action)
                archived_post.save()


class ForumPostHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=50)
    content = models.TextField()
    tags = models.CharField(max_length=150)
    date = models.DateTimeField(default=timezone.now)
    thread = models.UUIDField(db_index=True)
    author = models.UUIDField(db_index=True)
    row_action = models.CharField(max_length=10, default='ERROR')

    def __str__(self):
        return str(self.title)


class ForumComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    post = models.ForeignKey(
        ForumPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments')
    # CREATE, EDIT, DELETE - which put the row in this state?
    # (DELETE is used for Comment History)
    row_action = models.CharField(max_length=10, default='ERROR')

    def __str__(self):
        return str(self.content)[:20]

    def save(self, *args, **kwargs):
        save_method = self.row_action
        # all backups must complete properly for changes to be saved
        with transaction.atomic():
            # Do backup of current values in the row first.
            # (Note we backup before a DELETE.  Frequently,  a
            # row will have no backup history until we enter DELETE)
            # Rows will still be backed up even if 'ERROR' was assigned to the row_action.
            if save_method != "CREATE":
                original_comment = ForumComment.objects.get(pk=self.pk)
                comment_backup = ForumCommentHistory(comment_id=original_comment.id, content=original_comment.content, date=original_comment.date, post=original_comment.post.pk,
                                                     author=original_comment.author.pk, row_action=original_comment.row_action)
                comment_backup.save()

            # else: this is a newly created comment don't save it to backup table yet

            # No matter what happens,  save this new comment or comment update to the database.
            super().save(*args, **kwargs)

            # if this is a pre-delete save,  the comment row will have been updated to contain
            # 1) The action/method: "DELETE"
            # 2) The User who did the Delete
            # 3) The time of the deletion
            # We need to make sure this information is copied into comment history
            # before we delete the comment.
            # (If comment history needs to be totally deleted, that should be done
            # by a DBA)
            if save_method == 'DELETE':
                archived_comment = ForumCommentHistory(comment_id=self.id, content=self.content, date=self.date, post=self.post.pk,
                                                       author=self.author.pk, row_action=self.row_action)
                archived_comment.save()


class ForumCommentHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment_id = models.UUIDField(db_index=True)
    content = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    post = models.UUIDField(db_index=True)
    author = models.UUIDField(db_index=True)
    row_action = models.CharField(max_length=10, default='ERROR')


class ThreadRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
