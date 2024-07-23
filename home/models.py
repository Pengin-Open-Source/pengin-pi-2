from django.db import models
import uuid

    
class Home(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=100)
    article = models.TextField()
    image = models.CharField(max_length=200)
    tags = models.CharField(max_length=150)

    def __str__(self):
        return self.company_name