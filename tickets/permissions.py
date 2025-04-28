from django.db.models import OuterRef
from main.models.users import SubGroup, GroupToGroupAccess
from util.security.group_access import get_cross_group_access, get_super_groups, is_manager_of_this_role, can_access_group


def can_see_ticket(current_user, ticket):

    matching_role = can_access_group(current_user, ticket.role.id)

    return (current_user.is_staff or matching_role or current_user == ticket.author or is_ticket_manager(current_user, ticket))


def is_ticket_manager(current_user, ticket):
    return is_manager_of_this_role(current_user, ticket.role)
