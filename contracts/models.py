from django.db import models
import uuid


class Contract(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    customer = models.ForeignKey('Customer', on_delete=models.PROTECT, null=False)
    type = models.CharField(max_length=100)
    content = models.TextField()
    service_date = models.DateTimeField(null=True)
    expiration_date = models.DateTimeField(null=True)

    def __str__(self):
        return f"Contract {self.type} for {self.customer.name}"
