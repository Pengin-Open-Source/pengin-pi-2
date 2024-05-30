from django.db import models
import uuid

class About(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    image = models.CharField(max_length=100)
    twitter = models.CharField(max_length=100)
    facebook = models.CharField(max_length=100)
    instagram = models.CharField(max_length=100)
    whatsapp = models.CharField(max_length=100)
    linkedin = models.CharField(max_length=100)
    line = models.CharField(max_length=100)
    youtube = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    address1 = models.CharField(max_length=100)
    address2 = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    article = models.TextField()
    tags = models.CharField(max_length=150)

    def __str__(self):
        return self.name

class Home(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=100)
    article = models.TextField()
    image = models.CharField(max_length=200)
    tags = models.CharField(max_length=150)

    def __str__(self):
        return self.company_name