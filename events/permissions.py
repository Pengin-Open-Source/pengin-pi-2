from django.shortcuts import get_object_or_404

from .models import Event
from django.db.models import OuterRef
from main.models.users import SubGroup, GroupSpecialAccess
from util.security.group_access import get_cross_group_access, get_subgroups
SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']


def can_create_or_see_event(current_user, event_id=None):

    if event_id is None:
        return True
    # If the event exists, user has permission to see and duplicate it
    # if they are the event author, organizer, participant, or have a role associated with the event.
    # - or if they are staff.
    event = get_object_or_404(Event, id=event_id)
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
    matching_role = event.roles.filter(
        id__in=user_groups).exists() or event.roles.filter(
        id__in=user_super_groups.filter(ancestor=OuterRef('id'))).exists() or event.roles.filter(id__in=user_accessed_groups.filter(
            accessed_group=OuterRef('id'))).exists()

    participant_ids = event.participants.values_list(
        'participant_id', flat=True)

    return (current_user.is_staff or matching_role or current_user.id in participant_ids or current_user in [event.author,  event.organizer])


def can_change_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    # Only the author or organizer, or staff can change an event
    return request.user.is_staff or request.user in [event.author, event.organizer]
