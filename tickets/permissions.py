from django.db.models import OuterRef
from main.models.users import SubGroup, GroupSpecialAccess
from util.security.group_access import get_cross_group_access, get_subgroups


def can_see_ticket(current_user, ticket):

    user_groups = current_user.groups.all()

    # Retreive all the ancestor groups that the user's group is
    # a descendant of, using Subgroup closure table.
    user_super_groups = get_subgroups(user_groups)

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
    matching_role = ticket.roles.filter(
        id__in=user_groups).exists() or ticket.roles.filter(
        id__in=user_super_groups.filter(ancestor=OuterRef('id'))).exists() or ticket.roles.filter(id__in=user_accessed_groups.filter(
            accessed_group=OuterRef('id'))).exists()

    return (current_user.is_staff or matching_role or current_user == ticket.author)
