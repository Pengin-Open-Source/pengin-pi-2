from django.shortcuts import get_object_or_404

from .models import Event

SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']


def can_create_or_see_event(request, event_id=None):
    # If no event, user has all permissions
    if event_id is None:
        return True
    # If event exists, user has permission if they are the author, organizer, or a participant
    event = get_object_or_404(Event, id=event_id)
    return (request.user in [event.author, event.organizer]
            or request.user in event.participants.all())


def can_change_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    # Only the author or organizer cna change an event
    return request.user in [event.author, event.organizer]
