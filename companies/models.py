from django.db import models
import uuid


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    zipcode = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, unique=True)
    address1 = models.CharField(max_length=50)
    address2 = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class CompanyMembers(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return str(self.id)