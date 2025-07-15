from django.db.models import OuterRef
from main.models.users import SubGroup, GroupToGroupAccess, GroupManager, User
from django.db.models import Q
from django.contrib.auth.models import Group
# Credit to Google Gemini and Search AI for some suggestions for this file


def get_super_groups(groups):
    # Retreive all the ancestor groups that this set of groups is
    # a descendant of, using the Subgroup closure table.
    super_groups = SubGroup.objects.filter(
        descendant__in=groups).values('ancestor')
    return super_groups


def get_direct_parent(group):
    # TODO There SHOULD only be one result. Adding more than one parent
    # might cause unpleasant diamond problems. However
    # the current table logic doesn't prevent that.
    # Either fix that or provide some safety rails for dealing
    # with multiple parents.
    parents = SubGroup.objects.filter(
        descendant__in={group}).filter(depth=1).values('ancestor')

    parent_list = [id['ancestor'] for id in parents]
    parent = Group.objects.filter(id__in=parent_list).order_by('name').first()

    return parent


def get_sub_groups(groups):
    # Retreive all the descendant groups that this set of groups is
    # an ancestor of, using the Subgroup closure table.
    sub_groups = SubGroup.objects.filter(
        ancestor__in=groups).values('descendant')
    return sub_groups


def get_direct_children_of_group(group):
    children = SubGroup.objects.filter(
        ancestor__in={group}).filter(depth=1).values('descendant')
    child_list = [id['descendant'] for id in children]
    group_children = Group.objects.filter(id__in=child_list).order_by('name')

    return group_children


def is_a_manager(user_to_check):
    all_managers = get_group_managers()
    user_in_manager_queryset = all_managers.filter(manager=user_to_check)

    manages_anything = user_in_manager_queryset.exists()

    return manages_anything


def get_group_managers(groups=None):
    if groups:
        super_groups = get_super_groups(groups)
        group_managers = GroupManager.objects.filter(
            Q(managed_group__in=groups) | Q(
                managed_group__in=super_groups)).values('manager')
    else:
        group_managers = GroupManager.objects.all().values('manager')
    return group_managers


def get_cross_group_access(groups):
    # Retrieve all the groups that this set of groups has
    # cross-hierarchy access to, using the GroupToGroupAccess table
    # IMPORTANT. There is a KEY difference from being an actual member of
    # a group/role
    # If the user merely has special access to a role/group,  they do NOT also
    # INHERIT the permissions from the accessed group's ancestor roles
    accessed_groups = GroupToGroupAccess.objects.filter(
        group_with_access__in=groups).values('accessed_group')

    return accessed_groups


def get_all_groups_for_user_with_extended_rbac(given_user):
    user_groups = given_user.groups.all()

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

    group_list = [group.id for group in user_groups]
    super_group_list = [id['ancestor'] for id in user_super_groups]
    accesible_group_list = [id['accessed_group']
                            for id in user_accessed_groups]
    # all possible unique groups a user has RBAC to.
    combined_rbac_list = list(
        set(group_list + super_group_list + accesible_group_list))
    combined_rbac_queryset = Group.objects.filter(id__in=combined_rbac_list)
    return combined_rbac_queryset


def can_access_group(given_user, group_id):

    rbac_groups = get_all_groups_for_user_with_extended_rbac(given_user)
    matching_group = group_id in [group.id for group in rbac_groups]
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


def get_users_with_extended_rbac_to_group(role=None):
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


def is_manager_of_this_role(given_user, role):
    role_managers = get_group_managers({role})
    manager_uuids = [uuid['manager'] for uuid in role_managers]

    return given_user.id in manager_uuids
