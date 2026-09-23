##                   ##
#   UTILITY METHODS
##                   ##
from django.utils import timezone
from tickets.models import (
    TicketHistory,
    TicketCommentHistory,
    transaction,
)


def get_ticket_create_info(ticket):
    """
    Retrieves the original creation date of a ticket from its history.
    """

    oldest_date = ''
    is_create_missing = False

    ticket_history = TicketHistory.objects.filter(
        ticket=ticket.id,  row_action="CREATE")

    # there should be only one value.
    # we will set a flag if there is no row with method 'CREATE'  in TicketHistory
    oldest_ticket_record = ticket_history.first()

    if oldest_ticket_record:
        oldest_date = oldest_ticket_record.date
    else:
        # DBAs TAKE NOTE: If a DBA deletes some older Ticket History Records
        # then the row with the Ticket's initial creation date could have
        # been deleted and unavailable now!
        is_create_missing = True
        oldest_date = 'DATE NOT FOUND'
    return (oldest_date, is_create_missing)


# Since this method can have multiple operations that must succeed or fail together,
# I'm putting a transaction at the top of this method.
def delete_ticket(usr, archive_ticket):
    with transaction.atomic():
        archive_ticket.row_action = 'DELETE'
        archive_ticket.last_edited_by = usr
        archive_ticket.date = timezone.now()

        # First,  try to delete all the comments
        # If any deletion fails down the chain,  the whole deletion
        # process should be canceled.
        comments = archive_ticket.comments.all().order_by('-date')
        for comment in comments:
            delete_comment(usr, comment)

        # specify this is an deleted record
        # both save and delete must execute or fail together,
        # this keeps track of the time of deletion and
        # the user who deleted the record
        archive_ticket.save()
        archive_ticket.delete()
        return "success"


# Used to get original date/author of an edited comment
def get_comment_create_info(comment):
    oldest_date = ''
    is_create_missing = False

    comment_history = TicketCommentHistory.objects.filter(
        comment_id=comment.id,  row_action="CREATE")

    # there should be only one value.
    # we will set a flag if there is no row with method 'CREATE'  in Comment History
    oldest_comment_record = comment_history.first()
    if oldest_comment_record:
        oldest_date = oldest_comment_record.date
    else:
        # DBAs TAKE NOTE: If a DBA deletes some older Ticket Comment history records,
        # then the row with the TicketComment's initial creation date could have
        # been deleted and unavailable now!
        is_create_missing = True
        oldest_date = 'DATE NOT FOUND'
    return (oldest_date, is_create_missing)


def delete_comment(usr, archive_comment):
    """
    Archives and deletes a comment.
    This function does not use a transaction decorator itself, so it can be
    called from within another transaction (like delete_ticket) and allow
    failures to propagate up.
    """
    archive_comment.row_action = 'DELETE'
    archive_comment.last_edited_by = usr
    archive_comment.date = timezone.now()

    # specify this is an deleted record
    # both save and delete must execute or fail together,
    # this keeps track of the time of deletion and
    # the user who deleted the record
    archive_comment.save()
    archive_comment.delete()

    # Uncomment to test error in a transaction after both operations complete successfully
    # if "Comment about widgets" in archive_comment.content:
    #   raise TestTransactionError("Test Delete Comment Failure.")
    return "success"
