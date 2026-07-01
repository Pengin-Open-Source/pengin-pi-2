from django.apps import apps
from util.security.group_access import is_manager_of_this_role, is_a_manager,  can_access_group


def can_see_ticket(current_user, ticket):

    if can_edit_ticket(current_user, ticket):
        return True
    else:
        return can_access_group(current_user, ticket.role.id)


def can_edit_ticket_privileged(current_user, ticket):
    # only certain users can edit ALL the fields
    if current_user.is_staff:
        return True
    if is_ticket_manager(current_user, ticket):
        return True
    if current_user == ticket.owner:
        return True
    if current_user == ticket.author:
        return True


def can_edit_ticket(current_user, ticket):
    # To edit a ticket, the user must be
    # the author or owner of the ticket,
    # or be any kind of manager, or staff.
    # Or else,  the user must be part of a
    # related role AND the ticket must be open.
    # Note that not all users  who can edit,
    # can edit in the same way - see forms.py.

    if can_edit_ticket_privileged(current_user, ticket):
        return True

    if is_a_manager(current_user):
        return True

    # We might change this in the future if
    # more statuses are added.
    if ticket.resolution_status == 'open' or ticket.resolution_status == 'resolved':
        if can_access_group(current_user, ticket.role.id):
            return True

    return False


def can_open_ticket(current_user, ticket):
   # TODO pay careful attention to this method
   # and can_edit_ticket method if more
   # statuses are added. Think about how
   # how/if certain kinds of users can
   # move between the new statuses and
   # status 'Open'

    if can_edit_ticket_privileged(current_user, ticket):
        return True

    can_access_ticket_group = can_access_group(current_user, ticket.role.id)

    if can_access_ticket_group:
        # if the status is open, selecting the Open status isn't invalid :-)
        if ticket.resolution_status == 'open':
            return True

        # The user who moved the ticket from "Open" status to
        # "Resolved" status can reopen the ticket, if:
        #  a) that was the last status change &
        #  b) the user can still access the group.
        if is_user_who_resolved_ticket(current_user, ticket):
            return True

    return False


def can_close_ticket(current_user, ticket):
    if current_user.is_staff:
        return True
    if is_ticket_manager(current_user, ticket):
        return True

    return False


def can_edit_ticket_status(current_user, ticket):
    if can_close_ticket(current_user, ticket):
        return True
    if can_open_ticket(current_user, ticket):
        # remember this is True if the ticket is
        # already Open. This will allow user
        # to move an Open ticket to Resolved.
        return True

    # .... but if the Status is Resolved, some users
    # will not be able to change the Status directly.
    # (They may be able to Open it again by taking
    # ownership of the Ticket)
    # TODO add more cases, if necessary, when
    # new statuses are added to the program
    # ......

    return False


def can_comment_on_ticket(current_user, ticket):
    if ticket.resolution_status == 'closed':
        return can_edit_ticket_privileged(current_user, ticket)
    else:
        return can_edit_ticket(current_user, ticket)


def can_request_reopen(current_user, ticket):
    is_open_ticket = ticket.resolution_status == 'open'
    if is_open_ticket:
        return False

    user_has_pending_requests = current_user.reopen_ticket_requests.filter(
        approval_status='pending').filter(ticket=ticket)

    if user_has_pending_requests:
        return False
    return (not can_edit_ticket(current_user, ticket)) and can_see_ticket(current_user, ticket)


def is_ticket_manager(current_user, ticket):
    return is_manager_of_this_role(current_user, ticket.role)


def can_approve_this_reopen_request(current_user, reopen_request):

    if reopen_request.approval_status != 'pending':
        return False

    ticket = reopen_request.ticket
    return can_approve_reopen_requests_for_ticket(current_user, ticket)


def can_approve_reopen_requests_for_ticket(current_user, ticket):
    if current_user.is_staff:
        return True
    # only managers of THIS ticket's role can approve another request
    if is_ticket_manager(current_user, ticket):
        return True
    if current_user == ticket.owner:
        return True
    # note we don't let the author approve,  although they can reopen themselves.
    return False


def is_user_who_resolved_ticket(current_user, ticket):
    # If this ticket is in a Resolved state,  check to see who
    # resolved it.  If this ticket was altered in any other way
    # than commenting on it, or using the Status view to change
    # it to some non-open state, the ticket would have been Reopened.
    # Hence, if this state is Resolved, the last change must
    # have been to change it to a Status of Resolved.

    # TODO - Fix this comment and code if we decide to let
    # managers/staff move tickets between unrelated teams
    # they don't manage, WITHOUT automatically changing
    # the status.

    # TODO Also change this or add new methods as needed when/if
    # more status are added besides Open, Resolved and Closed

    if ticket.resolution_status != 'resolved' or ticket.last_edited_by != current_user:
        return False

    TicketHistory = apps.get_model('tickets', 'TicketHistory')

    ticket_history = TicketHistory.objects.filter(
        ticket=ticket.id)

    last_ticket_history_record = ticket_history.last()
    # if there's no history, this user didn't change it
    # last- or we have no way of confirming that they did.
    # (perhaps a resolved ticket was imported from another
    # system, or the dba deleted some ticket history data)
    if not last_ticket_history_record:
        return False
    elif last_ticket_history_record.resolution_status == 'open':
        # TODO unfortunately this logic will be messed up
        # if the user does a redundant Status update to
        # resolved.
        return True

    # if the last status wasn't Open,
    # or another user changed it, return False.
    return False
