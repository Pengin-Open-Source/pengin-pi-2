from django.db.models import OuterRef
from main.models.users import SubGroup, GroupToGroupAccess, GroupManager, User
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


def can_access_group(current_user, group_id):
    user_groups = current_user.groups.all()

    # Retrieve all the ancestor groups that the user's group is
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
    matching_group = (
        group_id in [group.id for group in user_groups] or
        group_id in [id['ancestor'] for id in user_super_groups] or
        group_id in [id['accessed_group'] for id in user_accessed_groups]

    )

    return matching_group


def get_validated_user_ids_with_access_to_group(group):
    # All users who are members of this role/group,
    # or a role with access to this group
    # (DOES NOT return THE GROUP MANAGER OR STAFF if they don't
    # have a related role)
    # Ideally,  the "validated" part of this should
    # be redundant - A user who is not validated
    # shouldn't have a role.
    validated_users = User.objects.filter(validated=True)
    who_can_access_role = []
    for user in validated_users:
        if can_access_group(user, group.id):
            who_can_access_role.append(user.id)

    return who_can_access_role


def get_valid_users_with_rbac(role=None):
    # Like get_validated_user_ids_with_access_to_group,
    # but here we use the ids to run a filter on the objects
    # This resulting queryset can be assigned direcly to
    # queryset of a picklist,  for example
    if role is None:
        users_with_rbac = User.objects.none()
    else:
        allowed_user_ids = get_validated_user_ids_with_access_to_group(
            role)

        users_with_rbac = User.objects.filter(
            id__in=allowed_user_ids)

    return users_with_rbac


def is_manager_of_this_role(current_user, role):
    role_managers = get_group_managers({role})
    manager_uuids = [uuid['manager'] for uuid in role_managers]

    return current_user.id in manager_uuids
