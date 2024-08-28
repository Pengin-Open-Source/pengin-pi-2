from django.db import models
from django.db import models, transaction
from django.conf import settings
from django.contrib.auth.models import Group
from main.models.users import User
from django.utils import timezone
import uuid


class Ticket(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    summary = models.CharField(max_length=100)
    content = models.TextField()
    tags = models.CharField(max_length=150)
    date = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='tickets')
    row_action = models.CharField(max_length=10, default='ERROR')
    resolution_status = models.CharField(max_length=100)
    resolution_date = models.CharField(max_length=100)

    def __str__(self):
        return str(self.summary)

    def save(self, *args, **kwargs):
        save_method = self.row_action
        super().save(*args, **kwargs)
