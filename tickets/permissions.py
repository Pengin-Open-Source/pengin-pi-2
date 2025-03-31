from django.db.models import OuterRef
from main.models.users import SubGroup, GroupToGroupAccess
from util.security.group_access import get_cross_group_access, get_super_groups, is_manager_of_this_role


def can_see_ticket(current_user, ticket):

    user_groups = current_user.groups.all()

    # Retreive all the ancestor groups that the user's group is
    # a descendant of, using Subgroup closure table.
    user_super_groups = get_super_groups(user_groups)

    # Retrieve all the groups that the user's groups has special access to,
    # using the GroupSpecialAccess table
    # IMPORTANT. This has a KEY difference from being an actual member of a group/role
    # If the user merely has special access to a role,  they do NOT also
    # inherit the permissions from this group's ancestor roles
    user_accessed_groups = get_cross_group_access(user_groups)

    # A matching role is a group/role assigned to this event where:
    # The user has this role
    # The user has a role that is a descendant role of this role.
    # The user has a role that can access this role
    matching_role = (
        ticket.role in [user_groups, user_super_groups,  user_accessed_groups])
    return (current_user.is_staff or matching_role or current_user == ticket.author)


def is_ticket_manager(current_user, ticket):

    is_manager_of_this_role(current_user, ticket.role)
