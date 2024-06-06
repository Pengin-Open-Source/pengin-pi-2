from django.db import models
import uuid
from datetime import datetime


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4())
    date = models.DateTimeField(null=True)
