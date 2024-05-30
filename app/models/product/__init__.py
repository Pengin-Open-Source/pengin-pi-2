from django.db import models
import uuid

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4())
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.CharField(max_length=100)
    article = models.TextField()
    card_image_url = models.CharField(max_length=500)
    stock_image_url = models.CharField(max_length=500)
    tags = models.CharField(max_length=150)
