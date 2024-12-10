from django.db import models
import uuid


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    address1 = models.CharField(max_length=50)
    address2 = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=50)
    zipcode = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    phone = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.address1}, {self.city}, {self.state}, {self.country}"
