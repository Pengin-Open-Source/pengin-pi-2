from django.db.models import OuterRef
from main.models.users import SubGroup, GroupToGroupAccess, GroupManager, User
from django.db.models import Q
from django.db.models.functions import Lower
from django.contrib.auth.models import Group

# Credit to Google Gemini and Search AI for some suggestions for this file


def get_super_groups(groups):
    # Retreive all the ancestor groups that this set of groups is
    # a descendant of, using the Subgroup closure table.
    ancestor_groups = SubGroup.objects.filter(
        descendant__in=groups).values('ancestor')

    super_group_list = [id['ancestor'] for id in ancestor_groups]
    super_groups = Group.objects.filter(
        id__in=super_group_list)
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
    parent = Group.objects.filter(
        id__in=parent_list).order_by(Lower('name')).first()

    return parent


def get_sub_groups(groups):
    # Retreive all the descendant groups that this set of groups is
    # an ancestor of, using the Subgroup closure table.
    descendant_groups = SubGroup.objects.filter(
        ancestor__in=groups).values('descendant')

    child_group_list = [id['descendant'] for id in descendant_groups]
    sub_groups = Group.objects.filter(
        id__in=child_group_list)

    return sub_groups


def get_direct_children_of_group(group):
    children = SubGroup.objects.filter(
        ancestor__in={group}).filter(depth=1).values('descendant')
    child_list = [id['descendant'] for id in children]
    group_children = Group.objects.filter(id__in=child_list)

    return group_children


def is_a_manager(user_to_check):
    # Unvalidated managers do not count/should have no privileges
    if not user_to_check.validated:
        return False

    manages_anything = False
    if hasattr(user_to_check, 'groups_managed') and user_to_check.groups_managed.exists():
        manages_anything = True

    return manages_anything


def get_groups_user_manages(user_to_check):
    # Treat unvalidated managers as though they didn't exist
    if not user_to_check.validated:
        return Group.objects.none()

    group_ids = user_to_check.groups_managed.values_list(
        'managed_group', flat=True)

    groups_user_manages_directly = Group.objects.filter(id__in=group_ids)

    managed_grandchildren = get_sub_groups(groups_user_manages_directly)

    return groups_user_manages_directly | managed_grandchildren


def get_group_managers(groups=None):
    if groups:
        super_groups = get_super_groups(groups)
        group_manager_objects = GroupManager.objects.filter(
            Q(managed_group__in=groups) | Q(
                managed_group__in=super_groups)).values('manager')
    else:
        group_manager_objects = GroupManager.objects.all().values('manager')

    manager_uuids = [uuid['manager'] for uuid in group_manager_objects]

    # Filter out any Manager who is not a *Validated* User
    group_managers = User.objects.filter(id__in=manager_uuids, validated=True)

    return group_managers


def get_non_tree_accessed_groups(groups):
    # NOTE that this gets all groups accessed by a SET of groups.
    # (but that set could at times have only one group)
    # Retrieve all the groups that this set of groups has
    # cross-hierarchy access to, using the GroupToGroupAccess table
    # IMPORTANT. There is a KEY difference from being an actual member of
    # a group/role
    # If the user merely has special access to a role/group,  they do NOT also
    # INHERIT the permissions from the accessed group's ancestor roles
    groups_accessed = GroupToGroupAccess.objects.filter(
        group_with_access__in=groups).values('accessed_group')

    accesible_group_list = [id['accessed_group']
                            for id in groups_accessed]
    accessed_groups = Group.objects.filter(
        id__in=accesible_group_list)

    return accessed_groups


def get_non_tree_accessor_groups(group):
    # Retrieve all the groups that have non-tree based access
    # TO a SINGLE group. Uses the GroupToGroupAccess table
    group_values_accessing_me = GroupToGroupAccess.objects.filter(
        accessed_group=group).values('group_with_access')

    group_ids_accessing_me_list = [id['group_with_access']
                                   for id in group_values_accessing_me]
    group_accessing_me = Group.objects.filter(
        id__in=group_ids_accessing_me_list)

    return group_accessing_me

# You can also access a group via group to group access
# or group inheritance,  but this lets you see/manage
# who is direct member of this group


def get_all_direct_group_members(group):
    group_members = User.objects.filter(
        validated=True).filter(groups__id=group.id)
    return group_members


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
    user_accessed_groups = get_non_tree_accessed_groups(user_groups)

    # A matching role is a group/role assigned to this event where:
    # The user has this role
    # The user has a role that is a descendant role of this role.
    # The user has a role that can access this role
    # all possible unique groups a user has RBAC to.

    combined_rbac_set = (user_groups | user_super_groups |
                         user_accessed_groups).distinct()
    return combined_rbac_set


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

    return given_user in role_managers
