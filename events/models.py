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
    # Leaving this as set null for now.  In a perfect world,  delete would trigger
    # an edit action which would create a backup BEFORE setting null,  but that's
    # not going to be coded now.
    added_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name='event_participants_added',  null=True)
    # setting on-delete to DO NOTHING. In theory DELETED rows should immediately go
    # into the archives (and deleted from this table). Thus deleted EventParticipant
    # objects should not available for the delete action on as User to trigger
    # any action on.
    deleted_by = models.ForeignKey(
        User, on_delete=models.DO_NOTHING,  null=True)
    row_action = models.CharField(max_length=10, default='ERROR')

    def __str__(self):
        return str(self.participant.name)


class EventParticipantHistory(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    event_participant_id = models.UUIDField(db_index=True)
    date = models.DateTimeField(auto_now_add=True)
    event = models.UUIDField(db_index=True)
    participant = models.UUIDField(db_index=True)
    # Leaving this as set null for now.  In a perfect world,  delete would trigger
    # an edit action which would create a backup BEFORE setting null,  but that's
    # not going to be coded now.
    added_by = models.UUIDField(db_index=True)
    # setting on-delete to DO NOTHING. In theory DELETED rows should immediately go
    # into the archives (and deleted from this table). Thus deleted EventParticipant
    # objects should not available for the delete action on as User to trigger
    # any action on.
    deleted_by = models.UUIDField(db_index=True)
    row_action = models.CharField(max_length=10, default='ERROR')

    def __str__(self):
        return str(self.participant.name)
