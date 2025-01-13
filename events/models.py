import uuid
from django.db import models
from django.contrib.auth.models import Group
from main.models import User


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    date = models.DateTimeField(auto_now_add=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    title = models.CharField(max_length=50)
    description = models.TextField()
    location = models.CharField(max_length=100)
    author = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="authored_events")
    organizer = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="organized_events")
    last_edited_by = models.ForeignKey(
        User,  on_delete=models.SET_NULL,  null=True)
    roles = models.ManyToManyField(Group, related_name='events', blank=True)
    row_action = models.CharField(max_length=10, default='ERROR')

    def __str__(self):
        return self.title + " at " + self.location

    def start_date(self):
        return self.start_datetime.date()

    def end_date(self):
        return self.end_datetime.date()

    def start_time(self):
        return self.start_datetime.time().strftime("%I:%M %p")

    def end_time(self):
        return self.end_datetime.time().strftime("%I:%M %p")


class EventParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateTimeField(auto_now_add=True)
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name='participants')
    participant = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='events')
    row_action = models.CharField(max_length=10, default='ERROR')
