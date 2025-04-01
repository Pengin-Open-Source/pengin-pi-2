from django.db.models import OuterRef
from main.models.users import SubGroup, GroupToGroupAccess, GroupManager
from django.db.models import Q
# Credit to Google Gemini and Search AI for some suggestiosn for this file


def get_super_groups(groups):
    # Retreive all the ancestor groups that this set of groups is
    # a descendant of, using the Subgroup closure table.
    super_groups = SubGroup.objects.filter(
        descendant__in=groups).values('ancestor')
    return super_groups


def get_sub_groups(groups):
    # Retreive all the descendant groups that this set of groups is
    # an ancestor of, using the Subgroup closure table.
    sub_groups = SubGroup.objects.filter(
        ancestor__in=groups).values('descendant')
    return sub_groups


def get_group_managers(groups):
    super_groups = get_super_groups(groups)
    group_managers = GroupManager.objects.filter(
        Q(managed_group__in=groups) | Q(
            managed_group__in=super_groups)).values('manager')
    return group_managers


def get_cross_group_access(groups):
    # Retrieve all the groups that this set of groups has cross-hierarchy access to,
    # using the GroupToGroupAccess table
    # IMPORTANT. There is a KEY difference from being an actual member of a group/role
    # If the user merely has special access to a role/group,  they do NOT also
    # INHERIT the permissions from the accessed group's ancestor roles
    accessed_groups = GroupToGroupAccess.objects.filter(
        group_with_access__in=groups).values('accessed_group')

    return accessed_groups


def is_manager_of_this_role(current_user, role):
    role_managers = get_group_managers({role})
    manager_uuids = [uuid['manager'] for uuid in role_managers]

    return current_user.id in manager_uuids
