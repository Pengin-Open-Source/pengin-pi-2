from django.db import models, transaction
import uuid
from django.utils import timezone


class BlogPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100, unique=True)
    date = models.DateTimeField(default=timezone.now)
    content = models.TextField(blank=True)
    tags = models.CharField(max_length=150,  blank=True)
    method = models.CharField(
        max_length=10, default='ERROR')

    # this will need to get replaced by db triggers OR Django Signals
    # If bulk actions are involved
    def save(self, *args, **kwargs):
        save_method = self.method
        with transaction.atomic():
            # Do backup of current row values first
            # DELETE is included because we will call save with save_method delete before calling delete
            if save_method == "EDIT" or save_method == "DELETE":
                original_post = BlogPost.objects.get(pk=self.pk)
                post_backup = BlogHistory(post_id=original_post.id, title=original_post.title,
                                          date=original_post.date, content=original_post.content, method=original_post.method, tags=original_post.tags)
                post_backup.save()
            # Else, if this is a newly created row don't save to backup table yet

            # save to this blog post table regardless
            super().save(*args, **kwargs)

            # if this is a pre-delete save,  we need to make sure the row we just saved in blogpost, which records
            # 1) The action/method: "DELETE"
            # 2) The time of the deletion
            # ... is saved into the bloghistory,  because our delete_post view is going to delete this information
            if save_method == 'DELETE':
                post_backup = BlogHistory(post_id=self.id, title=self.title,
                                          date=self.date, content=self.content, method=self.method, tags=self.tags)
                post_backup.save()

    def __str__(self):
        return str(self.title)


class BlogHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=100,  default='Error Getting Title')
    date = models.DateTimeField(default=timezone.now)
    content = models.TextField(blank=True)
    tags = models.CharField(max_length=150, blank=True)
    method = models.CharField(
        max_length=10, default='ERROR')
