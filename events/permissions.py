from django.shortcuts import get_object_or_404

from .models import Event

SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']


def can_create_or_see_event(current_user, event_id=None):
    # If no event, user has all permissions.
    if event_id is None:
        return True
    # If the event exists, user has permission to see and duplicate it
    # if they are the event author, organizer, participant, or have a role associated with the event.
    # - or if they are staff.

    event = get_object_or_404(Event, id=event_id)
    user_groups = current_user.groups.all()
    matching_roles = event.roles.filter(id__in=user_groups).exists()
    participant_ids = event.participants.values_list(
        'participant_id', flat=True)

    return (current_user.is_staff or matching_roles or current_user.id in participant_ids or current_user in [event.author,  event.organizer])


def can_change_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    # Only the author or organizer, or staff can change an event
    return request.user.is_staff or request.user in [event.author, event.organizer]
