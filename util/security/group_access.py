from django.db.models import OuterRef
from main.models.users import SubGroup, GroupSpecialAccess


def get_subgroups(groups):
    # Retreive all the ancestor groups that this set of groups is
    # a descendant of, using the Subgroup closure table.
    user_super_groups = SubGroup.objects.filter(
        descendant__in=groups).values('ancestor')
    return user_super_groups


def get_cross_group_access(groups):
    # Retrieve all the groups that this set of groups has special access to,
    # using the GroupSpecialAccess table
    # IMPORTANT. There is a KEY difference from being an actual member of a group/role
    # If the user merely has special access to a role/group,  they do NOT also
    # INHERIT the permissions from the accessed group's ancestor roles
    user_accessed_groups = GroupSpecialAccess.objects.filter(
        group_with_access__in=groups).values('accessed_group')

    return user_accessed_groups
