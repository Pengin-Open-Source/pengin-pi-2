import uuid
from django.db import models
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils import timezone
from main.models import User


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    date = models.DateTimeField(default=timezone.now)
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

    def save(self, *args, **kwargs):
        save_method = self.row_action
        # all backups must complete properly for changes to be saved
        with transaction.atomic():
            # Do backup of current values in the row first.
            # (Note we backup before a DELETE.  Frequently,  a
            # row will have no backup history until we enter DELETE)
            # Rows will still be backed up even if 'ERROR' was assigned to the row_action.
            if save_method != "CREATE":
                original_event = Event.objects.get(pk=self.pk)

                # KEY ASSUMPTION FOR THE FOLLOWING TO BE ACCURATE:
                # No one will change the groups-Event relationship, except by editing the Event
                # (IE,  adding or removing a Role from An Event, on An Event "Edit" page)
                # Also note that while the pk of group associated with an Event should not change,
                # it is theorectically possible for the NAME of group to change since the time it was
                # Linked to this Event (hence we save both in history)
                # NOTE THAT I equivocate between roles and groups and this time.
                event_roles = original_event.roles.all()
                groups_snapshot = list(event_roles.values('pk', 'name'))
                if original_event.last_edited_by:
                    event_editor = original_event.last_edited_by.pk
                else:
                    event_editor = None
                event_backup = EventHistory(event_id=original_event.pk, title=original_event.title, description=original_event.description,
                                            location=original_event.location, date=original_event.date,
                                            start_datetime=original_event.start_datetime, end_datetime=original_event.end_datetime,
                                            author=original_event.author.pk, organizer=original_event.organizer.pk, last_edited_by=event_editor,
                                            roles=groups_snapshot, row_action=original_event.row_action)
                event_backup.save()

            # else: this is a newly created Event; don't save it to backup table yet

            # In any event (but a rollback),  save this new Event or Event update to the database.
            super().save(*args, **kwargs)

            # if this is a pre-delete save,  the Event row will have been updated to contain
            # 1) The action/method: "DELETE"
            # 2) The User who did the Delete
            # 3) The time of the deletion
            # We need to make sure this information is copied into Event history
            # before we delete this Event.
            # (If Event history needs to be totally deleted, that should be done
            # by a DBA)
            if save_method == 'DELETE':
                # FYI, reusing groups_snapshot since it shouldn't have changed since the "last change" backup save
                archived_event = EventHistory(event_id=self.pk, title=self.title, description=self.description,
                                              location=self.location, date=self.date,
                                              start_datetime=self.start_datetime, end_datetime=self.end_datetime,
                                              author=self.author.pk, organizer=self.organizer.pk, last_edited_by=event_editor,
                                              roles=groups_snapshot, row_action=self.row_action)
                archived_event.save()


class EventHistory(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.UUIDField(db_index=True)
    date = models.DateTimeField()
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    title = models.CharField(max_length=50)
    description = models.TextField()
    location = models.CharField(max_length=100)

    # currently not allowing these two fields to be null,  since the Event table has these in on_delete PROTECT mode
    author = models.UUIDField(db_index=True)
    organizer = models.UUIDField(db_index=True)

    last_edited_by = models.UUIDField(db_index=True,  null=True)
    roles = models.JSONField()
    row_action = models.CharField(max_length=10, default='ERROR')


class EventParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateTimeField(default=timezone.now)
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

    def save(self, *args, **kwargs):
        save_method = self.row_action
        with transaction.atomic():

            # Do backup of the initally CREATEd row before we DELETE.
            # Since EventParticipants are currently only
            # CREATED and DELETEd,  not EDITed, and newly CREATEd rows don't get backups when they are created,
            # a row will have no backup history until it is deleted.
            # Also Rows will still be backed up even if 'ERROR' was assigned to the row_action.
            if save_method != "CREATE":
                event_participant_current = EventParticipant.objects.get(
                    pk=self.pk)

                # Check to see if the created_by field is null.
                # That can happen when the user who added the Member to the Company has been deleted from the system.
                if event_participant_current.added_by:
                    participant_adder = event_participant_current.added_by.pk
                else:
                    participant_adder = None

                event_participant_backup = EventParticipantHistory(event_participant_id=event_participant_current.id,
                                                                   event=event_participant_current.event.pk,
                                                                   participant=event_participant_current.participant.pk,
                                                                   date=event_participant_current.date,
                                                                   added_by=participant_adder,
                                                                   row_action=event_participant_current.row_action)
                event_participant_backup.save()

            super().save(*args, **kwargs)

            # Pre-delete save,  the EventParticipant row will have been updated to contain
            # 1) The action/method: "DELETE"
            # 2) The User who Deleted the EventParticipant in field deleted_by
            # 3) The time of the deletion
            # We need to make sure this information is copied into EventParticipantHistory
            # before we delete the EventParticipant
            # (If EventParticipantHistory needs to be totally deleted, that should be done
            # by a DBA)
            if save_method == 'DELETE':
                archived_participant = EventParticipantHistory(event_participant_id=self.id,
                                                               event=self.event.pk,
                                                               # Fyi, this value should always be here.
                                                               # The EventParticipant associated with a Deleted User does not get set null.
                                                               # Instead, deleting a User will CASCADE DELETE all the Event Participants
                                                               # associated with that user.
                                                               # So best practice is to delete the EventParticipant first, thus
                                                               # triggering this backup code, before deleting its User -
                                                               # - unless staff intends to wipe out all history associated with the user.
                                                               participant=self.participant.pk,
                                                               date=self.date,
                                                               added_by=participant_adder,
                                                               deleted_by=self.deleted_by.pk,
                                                               row_action=self.row_action)
                archived_participant.save()


class EventParticipantHistory(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    event_participant_id = models.UUIDField(db_index=True)
    date = models.DateTimeField()
    # Not allowing to be null as long as event and participant foreign keys
    # in EventParticipant are both CASCADE on delete,  and NOT NULL
    # (B/c that means there shouldn't be an Event or Participant field that is null in
    # those fields that we need to copy over)  But if that changes,  change here as well!
    event = models.UUIDField(db_index=True)
    participant = models.UUIDField(db_index=True)
    # Leaving this as set null for now.  In a perfect world,  delete would trigger
    # an edit action which would create a backup BEFORE setting null,  but that's
    # not going to be coded now.
    added_by = models.UUIDField(db_index=True,  null=True)
    # setting on-delete to DO NOTHING. In theory DELETED rows should immediately go
    # into the archives (and deleted from this table). Thus deleted EventParticipant
    # objects should not available for the delete action on as User to trigger
    # any action on.
    deleted_by = models.UUIDField(db_index=True, null=True)
    row_action = models.CharField(max_length=10, default='ERROR')

    def __str__(self):
        return str(self.participant.name)
