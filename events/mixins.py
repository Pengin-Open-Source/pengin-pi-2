
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.mixins import AccessMixin
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .permissions import is_month_too_far_away
from events.models import Event
from .calendar import filter_events


class PublicEventsOrLoggedInMixin(AccessMixin):

    def dispatch(self, request, *args, **kwargs):
        selected_year = self.kwargs.get("year")
        selected_month = self.kwargs.get("month")

        # is the the Calendar View? Ff so, find out if
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

        public_events_within_a_year = filter_events(
            Event.objects.filter(is_public=True), [])
        if public_events_within_a_year:
            return super().dispatch(request, *args, **kwargs)
        else:
            selected_event = self.kwargs.get("event_id")

            # trying to access a specific event, or the calendar?
            if selected_event:
                error_message = "<h1> <center> Event Not Available </center> </h1>"
            else:
                error_message = "<h1> <center> No Public Events Available At This Time </center> </h1>"
            return HttpResponseForbidden(error_message)
