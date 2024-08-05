from django.db import models
import uuid

from main.models import User
from forums.models import Role  # Role should be in the main app, not in forums


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    date_created = models.DateTimeField(auto_now_add=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    title = models.CharField(max_length=50)
    description = models.TextField()
    location = models.CharField(max_length=100)
    author = models.ForeignKey(User, on_delete=models.PROTECT, related_name="authored_events")
    organizer = models.ForeignKey(User, on_delete=models.PROTECT, related_name="organized_events")
    participants = models.ManyToManyField(User, related_name="events")
    role = models.ForeignKey(Role, on_delete=models.PROTECT)

    def __str__(self):
        return self.title + " at " + self.location

    def start_date(self):
        return self.start_datetime.date()

    def end_date(self):
        return self.end_datetime.date()

    def start_time(self):
        return self.start_datetime.time().strftime("%H:%M")

    def end_time(self):
        return self.end_datetime.time().strftime("%H:%M")
