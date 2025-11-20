
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.mixins import AccessMixin
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .permissions import is_month_too_far_away, is_any_public_event_available, can_see_public_event
from events.models import Event


class PublicEventsOrLoggedInMixin(AccessMixin):

    def dispatch(self, request, *args, **kwargs):
        selected_year = self.kwargs.get("year")
        selected_month = self.kwargs.get("month")

        # is the the Calendar View? If so, find out if
        # we're trying to look too far into the future
        # or past for an Anonymous User.

        if request.user.is_authenticated:
            if request.user.validated:
                return super().dispatch(request, *args, **kwargs)
        else:
            if (selected_year and selected_month) and is_month_too_far_away(selected_year, selected_month):
                return HttpResponseForbidden("<h1> <center> Cannot View Events This Far From Today </center> </h1>")

            # if we passed the validated user check, the only events
            # available are public events within a year of today.

        event_id = self.kwargs.get("event_id")
        # if the user is trying to access a specific event:
        if event_id:
            selected_event = Event.objects.get(id=event_id)
            # is this a public event,  and
            # is it within a year from now?
            if can_see_public_event(selected_event):
                return super().dispatch(request, *args, **kwargs)
            else:
                return HttpResponseForbidden("<h1> <center> Event Not Available </center> </h1>")

        # User isn't logged in, but is trying to see the calendar
        # Are there ANY public events within a year from now,
        # (year past or year in future)? If not,  don't let this
        # user see the calendar
        if is_any_public_event_available():
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("<h1> <center> No Public Events Available At This Time </center> </h1>")
