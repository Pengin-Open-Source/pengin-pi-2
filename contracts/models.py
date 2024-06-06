from django.db import models
import uuid
from datetime import datetime, timezone


class Contracts(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4())
    contract_type = models.CharField(max_length=100)
    content = models.TextField()
    service_date = models.DateTimeField(null=True)
    expiration_date = models.DateTimeField(null=True)
