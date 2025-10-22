from util.security.group_access import is_manager_of_this_role, is_a_manager,  can_access_group


def can_see_ticket(current_user, ticket):

    if can_edit_ticket(current_user, ticket):
        return True
    else:
        return can_access_group(current_user, ticket.role.id)


def can_edit_ticket(current_user, ticket):
    # To edit a ticket, the user must be
    # the author or owner of the ticket,
    # or be any kind of manager, or staff.
    # Or else,  the user must be part of a
    # related role AND the ticket must be open.
    # Note that not all users  who can edit,
    # can edit in the same way - see forms.py.

    if current_user.is_staff:
        return True
    if is_a_manager(current_user):
        return True
    if current_user == ticket.owner:
        return True
    if current_user == ticket.author:
        return True
    if ticket.resolution_status == 'open':
        if can_access_group(current_user, ticket.role.id):
            return True

    return False


def can_comment_on_ticket(current_user, ticket):
    # currently whoever can edit the ticket can comment on it.
    # so this is redundant right now.
    # But if that changes,  we just have to change the logic here
    can_edit_ticket(current_user, ticket)


def can_request_reopen(current_user, ticket):
    is_open_ticket = ticket.resolution_status == 'open'
    return (not is_open_ticket) and not can_edit_ticket(current_user, ticket) and can_see_ticket(current_user, ticket)


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
