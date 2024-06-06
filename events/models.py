from django.db import models
import uuid
from datetime import datetime
from django.utils.timezone import now


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    start_datetime = models.DateTimeField(null=False)
    end_datetime = models.DateTimeField(null=False)
    title = models.CharField(max_length=50)
    description = models.TextField(max_length=5000)
    location = models.CharField(max_length=50)

    def __repr__(self):  # for debug purpose
        return f"(id: {self.id}, title: {self.title}, desc: {self.description}, location: {self.location}, start_datetime: {self.start_datetime}, end_datetime: {self.end_datetime}, created_at: {self.date_created})\t"

    def add_time(self):
        self.start_time = datetime.time(self.start_datetime).strftime("%H:%M")
        self.end_time = datetime.time(self.end_datetime).strftime("%H:%M")

    def add_date(self):
        self.start_date = datetime.date(self.start_datetime)
        self.end_date = datetime.date(self.end_datetime)

    def __str__(self):
        return str(self.title)
