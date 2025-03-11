from django.shortcuts import get_object_or_404

from .models import Event

SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']


def can_create_or_see_event(request, event_id=None):
    # If no event, user has all permissions
    if event_id is None:
        return True
    # If event exists, user has permission if they are the author, organizer, or a participant - or staff
    # Participants have permission to a) See Events they are in  b) duplicate events they are in
    event = get_object_or_404(Event, id=event_id)
    participant_ids = event.participants.values_list(
        'participant_id', flat=True)

    return (request.user.is_staff or request.user.id in participant_ids or request.user in [event.author,  event.organizer])


def can_change_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    # Only the author or organizer, or staff can change an event
    return request.user.is_staff or request.user in [event.author, event.organizer]
