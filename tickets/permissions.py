from util.security.group_access import is_manager_of_this_role, is_a_manager,  can_access_group


def can_see_ticket(current_user, ticket):

    has_a_matching_role = can_access_group(current_user, ticket.role.id)

    is_a_group_manager = is_a_manager(current_user)
    is_assigned_to_ticket = current_user == ticket.owner
    is_author = current_user == ticket.author
    return (current_user.is_staff or has_a_matching_role or is_author or is_assigned_to_ticket or is_a_group_manager)


def can_edit_ticket(current_user, ticket):
    # At the moment,  this is redundant with can_see_ticket,
    # since the current logic allows a user to edit any ticket it can see
    # (although not all users can edit in the same way - see forms.py).
    # However, some day we may switch to blocking some users who can VIEW
    # tickets from actually EDITing them. In that case, we can just revisit
    # the logic here in this one method.
    return can_see_ticket(current_user, ticket)


def is_ticket_manager(current_user, ticket):
    return is_manager_of_this_role(current_user, ticket.role)
