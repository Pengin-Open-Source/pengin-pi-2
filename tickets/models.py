from django.db import models
from django.db import models, transaction
from django.contrib.auth.models import Group
from main.models.users import User
from django.utils import timezone
import uuid
from tickets.permissions import can_see_ticket


class TicketQuerySet(models.QuerySet):
    # Custom QuerySet for the Ticket Model
    # - as per recommended approach from Google Gemini
    # when you need to filter using a custom function

    def filter_by_can_see_ticket(self, user):
        results = []
        for ticket in self:
            if can_see_ticket(user, ticket):
                results.append(ticket.id)
        self.filter(id__in=results)
        return self.filter(id__in=results)


class TicketManager(models.Manager):
    # Custom Manager for the Custom Ticket QuerySet
    # - as per recommended approach from Google Gemini
    # when you need to filter using a custom function

    def get_queryset(self):
        return TicketQuerySet(self.model, using=self._db)

    def filter_by_can_see_ticket(self, user):
        return self.get_queryset().filter_by_can_see_ticket(user)


class Ticket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    summary = models.CharField(max_length=100)
    content = models.TextField()
    tags = models.CharField(max_length=150)
    date = models.DateTimeField(default=timezone.now)
    # Warning: Cascade deletes won't save unedited tickets to history!
    # They also will not delete any edited tickets FROM history.
    # This class might need to be used with signals at some point
    # If the person who made the ticket is deleted from the system,
    # Cascade delete the ticket
    # If it's the person who edited it last, set the value to null.
    # If the person who OWNS the ticket the ticket is set to be deleted, block him!
    # The ticket must be owned,  and someone must recieve ownership of the issue
    # before the ticket can be deleted
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='tickets_authored')
    owner = models.ForeignKey(
        User, on_delete=models.RESTRICT, related_name='tickets_owned', null=True,  blank=True)
    last_edited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,  null=True)
    row_action = models.CharField(max_length=10, default='ERROR')
    resolution_status = models.CharField(max_length=100)
    resolution_date = models.DateTimeField(null=True, blank=True)
    role = models.ForeignKey(
        Group, on_delete=models.RESTRICT, related_name='tickets')

    objects = TicketManager.from_queryset(TicketQuerySet)()

    def __str__(self):
        return str(self.summary)

    def save(self, *args, **kwargs):
        save_method = self.row_action

        # all backups must complete properly for changes to be saved
        with transaction.atomic():
            # Do backup of current values in the row first.
            # (Note we backup before a DELETE.  Frequently,  a
            # Ticket row will have no backup history until we enter DELETE)
            # Rows will still be backed up even if 'ERROR' was assigned to the row_action.
            if save_method != "CREATE":
                original_ticket = Ticket.objects.get(pk=self.pk)
                # ticket_roles = original_ticket.roles.all()
                # group_snapshot = list(
                #    original_ticket.role.values('pk', 'name'))
                group_snapshot = [
                    {'pk': original_ticket.role.pk, 'name': original_ticket.role.name}]
                if original_ticket.last_edited_by:
                    last_editor = original_ticket.last_edited_by.pk
                else:
                    last_editor = None
                if original_ticket.owner:
                    ticket_owner = original_ticket.owner.pk
                else:
                    ticket_owner = None

                ticket_backup = TicketHistory(ticket_id=original_ticket.id, summary=original_ticket.summary, content=original_ticket.content,  tags=original_ticket.tags, date=original_ticket.date,
                                              author=original_ticket.author.pk, owner=ticket_owner, last_edited_by=last_editor, row_action=original_ticket.row_action, resolution_status=original_ticket.resolution_status,
                                              resolution_date=original_ticket.resolution_date, role=group_snapshot)
                ticket_backup.save()

            # else: this is a newly created Ticket don't save it to backup table yet

            # In any event (but a rollback),  save this new ticket or post ticket to the database.

        super().save(*args, **kwargs)

        # if this is a pre-delete save,  the ticket row will have been updated to contain
        # 1) The action/method: "DELETE"
        # 2) The User who did the Delete
        #    (saved in last_edited_by.  So I am not checking
        #    since it SHOULD always be here)
        # 3) The time of the deletion
        # We need to make sure this information is copied into Ticket history
        # before we delete the Ticket.
        # (If Ticket history needs to be totally deleted, that should be done
        # by a DBA)

        # Make sure we handle the case where
        # where the ticket was never assigned to anyone
        if self.owner:
            deleted_ticket_owner = self.owner.pk
        else:
            deleted_ticket_owner = None

        if save_method == 'DELETE':
            archived_ticket = TicketHistory(ticket_id=self.pk, summary=self.summary, content=self.content,  tags=self.tags, date=self.date,
                                            author=self.author.pk, owner=deleted_ticket_owner,  last_edited_by=self.last_edited_by.pk, row_action=self.row_action, resolution_status=self.resolution_status,
                                            resolution_date=self.resolution_date, role=group_snapshot)

            archived_ticket.save()


class TicketHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_id = models.UUIDField(db_index=True)
    summary = models.CharField(max_length=100)
    content = models.TextField()
    tags = models.CharField(max_length=150)
    date = models.DateTimeField(default=timezone.now)
    author = models.UUIDField(db_index=True)
    owner = models.UUIDField(db_index=True, null=True)
    last_edited_by = models.UUIDField(db_index=True, null=True)
    row_action = models.CharField(max_length=10, default='ERROR')
    resolution_status = models.CharField(max_length=100)
    resolution_date = models.DateTimeField(null=True, blank=True)
    role = models.JSONField()

    def __str__(self):
        return str(self.summary)


class TicketComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='ticket_comments')
    last_edited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,  null=True)
    # CREATE, EDIT, DELETE - which put the row in this state?
    # (DELETE is used for Comment History)
    row_action = models.CharField(max_length=10, default='ERROR')

    def __str__(self):
        return str(self.content)[:20]

    def save(self, *args, **kwargs):
        save_method = self.row_action

        with transaction.atomic():
            # Do backup of current values in the row first.
            # (Note we backup before a DELETE.  Frequently,  a
            # Comment row will have no backup history until we enter DELETE)
            # Rows will still be backed up even if 'ERROR' was assigned to the row_action.
            if save_method != "CREATE":

                original_comment = TicketComment.objects.get(pk=self.pk)
                if original_comment.last_edited_by:
                    comment_backup = TicketCommentHistory(comment_id=original_comment.id, content=original_comment.content, date=original_comment.date, ticket=original_comment.ticket.pk,
                                                          author=original_comment.author.pk, last_edited_by=original_comment.last_edited_by.pk, row_action=original_comment.row_action)
                else:
                    comment_backup = TicketCommentHistory(comment_id=original_comment.id, content=original_comment.content, date=original_comment.date, ticket=original_comment.ticket.pk,
                                                          author=original_comment.author.pk, row_action=original_comment.row_action)
                comment_backup.save()

            # else: this is a newly created comment don't save it to backup table yet

            # No matter what happens,  save this new comment or comment update to the database.
            super().save(*args, **kwargs)

            # if this is a pre-delete save,  the comment row will have been updated to contain
            # 1) The action/method: "DELETE"
            # 2) The User who did the Delete
            # 3) The Author of the comment
            # 4) The time of the deletion
            # We need to make sure this information is copied into comment history
            # before we delete the comment.
            # (If comment history needs to be totally deleted, that should be done
            # by a DBA)
            if save_method == 'DELETE':
                archived_comment = TicketCommentHistory(comment_id=self.id, content=self.content, date=self.date, ticket=self.ticket.pk,
                                                        author=self.author.pk, last_edited_by=self.last_edited_by.pk, row_action=self.row_action)
                archived_comment.save()

        super().save(*args, **kwargs)


class TicketCommentHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment_id = models.UUIDField(db_index=True)
    content = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    ticket = models.UUIDField(db_index=True)
    author = models.UUIDField(db_index=True)
    last_edited_by = models.UUIDField(db_index=True, null=True)
    row_action = models.CharField(max_length=10, default='ERROR')


class TicketOpenRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reason = models.TextField()
    request_date = models.DateTimeField(default=timezone.now)
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name='reopen_requests')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reopen_ticket_requests')
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reopen_ticket_requests_handled', null=True, blank=True)
    # CREATE, EDIT DELETE - which put the row in this state?)
    # (DELETE is used for TicketOpenRequestHistory. )
    # Edit will at least be used by the reviewer.
    # At the moment,  Author is not allowed to edit, so as to
    # prevent changing of the reason for the re-open request.
    row_action = models.CharField(max_length=10, default='ERROR')
    # 'pending' 'approved' 'denied 'reopened by other user'
    approval_status = models.CharField(max_length=100, default='pending')
    reviewer_comment = models.TextField(null=True,  blank=True)
    date_handled = models.DateTimeField(null=True, blank=True)
    # if some other request resulted in a reopen,  making this request obsolete/de facto granted.
    # I don't think we want to cascade delete all requests
    related_request_approved = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='side_effect_approved_requests'
    )
    # TODO:  Find out what should happen if a ticket status is changed
    # to a value that is Neither Open nor Closed (Like "Resolved")
    # If a user 1) Directly changed the status of the Ticket to Open.
    #           2) Edited the ticket and caused a side-effect reopen
    #           3) Commented on the ticket and caused a side-effect reopen
    # ... then NO user actually directly approved a request to reopen the
    # ticket;  the approval process was bypassed.
    bypass_initiated_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bypassed_reopen_requests', null=True, blank=True)

    def __str__(self):
        return "Reopen Request From: " + self.author.name + " " + str(self.reason)[:20]
