from django.db import models
from django.db import models, transaction
from django.conf import settings
from django.contrib.auth.models import Group
from main.models.users import User
from django.utils import timezone
import uuid


class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    summary = models.CharField(max_length=100)
    content = models.TextField()
    tags = models.CharField(max_length=150)
    date = models.DateTimeField(default=timezone.now)
    # Warning: Cascade deletes won't save unedited tickets to history!
    # They also will not delete any edited tickets FROM history.
    # This class might need to be used with signals at some point
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='tickets')
    last_edited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,  null=True)
    row_action = models.CharField(max_length=10, default='ERROR')
    resolution_status = models.CharField(max_length=100)
    resolution_date = models.CharField(max_length=100)

    def __str__(self):
        return str(self.summary)

    def save(self, *args, **kwargs):
        save_method = self.row_action

        # all backups must complete properly for changes to be saved
        with transaction.atomic():
            # Do backup of current values in the row first.
            # (Note we backup before a DELETE.  Frequently,  a
            # row will have no backup history until we enter DELETE)
            # Rows will still be backed up even if 'ERROR' was assigned to the row_action.
            if save_method != "CREATE":
                original_ticket = Ticket.objects.get(pk=self.pk)
                if original_ticket.last_edited_by:
                    ticket_backup = TicketHistory(ticket_id=original_ticket.id, summary=original_ticket.summary, content=original_ticket.content,  tags=original_ticket.tags, date=original_ticket.date,
                                                  author=original_ticket.author.pk, last_edited_by=original_ticket.last_edited_by.pk, row_action=original_ticket.row_action, resolution_status=original_ticket.resolution_status,
                                                  resolution_date=original_ticket.resolution_date)
                else:
                    ticket_backup = TicketHistory(ticket_id=original_ticket.id, summary=original_ticket.summary, content=original_ticket.content,  tags=original_ticket.tags, date=original_ticket.date,
                                                  author=original_ticket.author.pk, row_action=original_ticket.row_action, resolution_status=original_ticket.resolution_status, resolution_date=original_ticket.resolution_date)

                ticket_backup.save()

            # else: this is a newly created post don't save it to backup table yet

            # In any event (but a rollback),  save this new post or post update to the database.

        super().save(*args, **kwargs)

        # DELETE CODE GOES HERE......


class TicketHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_id = models.UUIDField(db_index=True)
    summary = models.CharField(max_length=100)
    content = models.TextField()
    tags = models.CharField(max_length=150)
    date = models.DateTimeField(default=timezone.now)
    author = models.UUIDField(db_index=True)
    last_edited_by = models.UUIDField(db_index=True, null=True)
    row_action = models.CharField(max_length=10, default='ERROR')
    resolution_status = models.CharField(max_length=100)
    resolution_date = models.CharField(max_length=100)

    def __str__(self):
        return str(self.summary)


class TicketComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(
        User, on_delete=models.DO_NOTHING)
    # CREATE, EDIT, DELETE - which put the row in this state?
    # (DELETE is used for Comment History)
    row_action = models.CharField(max_length=10, default='ERROR')

    def __str__(self):
        return str(self.content)[:20]

    def save(self, *args, **kwargs):
        save_method = self.row_action
        super().save(*args, **kwargs)
