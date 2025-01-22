from zoneinfo import ZoneInfo
# Have to specify package for "timezone" b/c I'm importing two differant timezones
from datetime import datetime, timezone as dt_timezone
from django.utils import timezone as django_timezone
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render, reverse, get_object_or_404, redirect
from django.views import View
from main.mixins import LoginAndValidationRequiredMixin
from .models import Event, EventParticipant

from .calendar import EventCalendar
from .forms import EventForm, CalendarSettingsForm
from .permissions import can_create_or_see_event, can_change_event


myCal = EventCalendar()


class CalendarMonth(LoginAndValidationRequiredMixin, View):
    template_name = "calendar/calendar_month.html"

    def get(self, request, year=None, month=None):
        another_time_zone_str = request.session.get('time_zone_string')
        user_time_zone_str = request.COOKIES.get('time_zone')
        # if the cookie is not available yet,  try the session variable...
        if not user_time_zone_str:
            user_time_zone_str = another_time_zone_str
        myCal.set_time_zone(user_time_zone_str)

        present_datetime = datetime.now()
        # Using local present time for the calendar month
        # becomes relevant on the first and last days of months
        # and years
        present_local_time = convert_to_local(
            # - * actual local time, not another masquerade for flatpickr
            present_datetime, user_time_zone_str)
        present_year = present_local_time.year
        present_month = present_local_time.month

        if year is None or month is None:
            year = present_year
            month = present_month

        if not myCal.user_settings:
            myCal.setfirstweekday(6)

        calendar_html = myCal.formatmonth(int(year), int(
            month), withyear=True, current_user=request.user)

        def get_previous_month():
            if int(month) == 1:
                return {"year": int(year) - 1, "month": 12}
            return {"year": year, "month": int(month) - 1}

        def get_next_month():
            if int(month) == 12:
                return {"year": int(year) + 1, "month": 1}
            return {"year": year, "month": int(month) + 1}

        previous_month = get_previous_month()
        next_month = get_next_month()

        url_previous_month = reverse(
            "calendar:calendar-month",
            kwargs={
                "year": previous_month["year"],
                "month": previous_month["month"],
            },
        )
        url_present_month = reverse(
            "calendar:calendar-month",
            kwargs={
                "year": present_year,
                "month": present_month,
            },
        )
        url_next_month = reverse(
            "calendar:calendar-month",
            kwargs={
                "year": next_month["year"],
                "month": next_month["month"],
            },
        )

        return render(
            request,
            self.template_name,
            {
                "primary_title": "Calendar",
                "calendar_html": calendar_html,
                "url_previous_month": url_previous_month,
                "url_present_month": url_present_month,
                "url_next_month": url_next_month,
                "currentUser": request.user,
            },
        )


class DetailEvent(LoginAndValidationRequiredMixin, UserPassesTestMixin, View):
    template_name = "calendar/event_detail.html"

    def test_func(self):
        return can_create_or_see_event(self.request, self.kwargs.get("event_id"))

    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        # - turn the event's utc datetime into a local datetime
        user_time_zone_str = self.request.COOKIES.get('time_zone')
        event.start_datetime = convert_to_masquerade_local(
            event.start_datetime, user_time_zone_str)
        event.end_datetime = convert_to_masquerade_local(
            event.end_datetime, user_time_zone_str)
        return render(
            request,
            self.template_name,
            {
                "primary_title": event.title,
                "event": event,
                "can_change": can_change_event(request, event_id)
            },
        )


class CreateEvent(LoginAndValidationRequiredMixin, UserPassesTestMixin, View):
    model = Event
    form_class = EventForm
    template_name = "calendar/event_form.html"

    def test_func(self):
        return can_create_or_see_event(self.request, self.kwargs.get("event_id"))

    def get(self, request, *args, **kwargs):
        form = EventForm()
        form_rendered_for_create = form.render(
            "configure_event_form.html")
        context = {
            "primary_title": "Create Event",
            "action": "create",
            "form": form_rendered_for_create,

        }
        return render(request, self.template_name, context)

    def post(self, request, **kwargs):
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.author = request.user
            event.row_action = 'CREATE'

            # See EditEvent's post method for details
            user_time_zone_str = request.COOKIES.get('time_zone')
            event.start_datetime = convert_to_utc(
                event.start_datetime, user_time_zone_str)
            event.end_datetime = convert_to_utc(
                event.end_datetime, user_time_zone_str)

            event.save()

            for attendee in form.participants_to_add:
                EventParticipant.objects.create(
                    event=event, participant=attendee,  row_action='CREATE')

            return redirect("calendar:calendar")

        form_rendered_for_create = form.render("configure_event_form.html")
        context = {
            "primary_title": "Create Event",
            "action": "create",
            "form": form_rendered_for_create,

        }
        return render(request, self.template_name, context)


class EditEvent(LoginAndValidationRequiredMixin, UserPassesTestMixin, View):
    template_name = "calendar/event_form.html"

    def test_func(self):
        return can_change_event(self.request, self.kwargs.get("event_id"))

    def get_context_data(self):
        event = get_object_or_404(Event, id=self.kwargs["event_id"])
        # reverse of what we do in post method
        # - turn the event's utc datetime into a local datetime
        user_time_zone_str = self.request.COOKIES.get('time_zone')
        event.start_datetime = convert_to_masquerade_local(
            event.start_datetime, user_time_zone_str)
        event.end_datetime = convert_to_masquerade_local(
            event.end_datetime, user_time_zone_str)

        form = EventForm(instance=event)

        form_rendered_for_edit = form.render("configure_event_form.html")

        return {
            "primary_title": "Edit Event",
            "action": "update",
            "form": form_rendered_for_edit,
            "event": event,
        }

    def get(self, request, event_id):
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            event = form.save(commit=False)
            event.last_edited_by = request.user
            event.date = django_timezone.now()
            event.row_action = 'EDIT'

            # () Working with Google's AI and also referring to Flask version for this)
            # - Grab the timezone that was stored as a cookie in layout.html,  convert
            # the time into the correct UTC time.
            # The reason we are converting a date that is already utc into utc,
            # is because the user THINKS they entered the date time in their own timezone.
            # We need to do some tweaks to get the transformation right.
            user_time_zone_str = request.COOKIES.get('time_zone')
            event.start_datetime = convert_to_utc(
                event.start_datetime, user_time_zone_str)
            event.end_datetime = convert_to_utc(
                event.end_datetime, user_time_zone_str)

            event.save()
            for attendee in form.participants_to_add:
                EventParticipant.objects.create(
                    event=event, participant=attendee,  row_action='EDIT')

            for not_attending in form.delete_participants:
               # deleteMe =  EventParticipant.objects.get(event=event, participant=not_attending)
                deleteMe = get_object_or_404(
                    EventParticipant, event=event, participant=not_attending)
                deleteMe.delete()

            return redirect("calendar:detail-event", event_id=event.id)

        context = self.get_context_data()
        context["form"] = form
        return render(request, self.template_name, context)


class DeleteEvent(LoginAndValidationRequiredMixin, UserPassesTestMixin, View):
    template_name = "calendar/event_confirm_delete.html"

    def test_func(self):
        return can_change_event(self.request, self.kwargs.get("event_id"))

    def get(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        context = {
            "primary_title": f"Delete Event: {event.title}",
            "event": event,
        }
        return render(request, self.template_name, context)

    def post(self, request, event_id):
        event = get_object_or_404(Event, id=event_id)
        event.delete()
        return redirect('calendar:calendar')


class CalendarSettings(LoginAndValidationRequiredMixin, View):
    template_name = "calendar/calendar_settings.html"

    def get(self, request):
        context = {}

        selected_weekday = myCal.firstweekday
        form = CalendarSettingsForm(
            initial={'first_day_of_week': selected_weekday})
        context["form"] = form
        context["primary_title"] = "Calendar Settings"
        return render(request, self.template_name, context)

    def post(self, request):
        form = CalendarSettingsForm(request.POST)
        if form.is_valid():
            first_day_cal = int(form.cleaned_data['first_day_of_week'])
            myCal.setfirstweekday(first_day_cal)
            myCal.user_settings = True
            return redirect('calendar:calendar')

        context = {}
        context["form"] = form
        return render(request, self.template_name, context)


################### UTILITY METHODS #########################

def convert_to_utc(event_datetime,  time_zone_str):
    """Converts a local datetime object to UTC."""
    # IMPORTANT - the User THINKS the date is in their time zone, but it's actually UTC
    # Therefore,  we must replace (not convert) the date's timezone to be whatever timezone
    # the user is in.  Then we can convert to the real Universal Time equivalent
    # So, if the user selects a start date of 10:00 AM,  they may THINK
    # that the chose 10:00 AM EST or EDT - but it's actually UTC.  In order to put the real UTC time
    # that would actually equate to 10:00 AM EST or EDT in the database,  we need to first
    # change the time to 10:00 AM America/New York, and then convert that time to UTC

    user_time_zone = ZoneInfo(time_zone_str)
    local_time = event_datetime.replace(tzinfo=user_time_zone)

    return local_time.astimezone(dt_timezone.utc)


def convert_to_local(event_datetime, time_zone_str):
    """ Convert utc datetime to local datetime """

    user_time_zone = ZoneInfo(time_zone_str)
    # convert utc to local.
    local_time = event_datetime.astimezone(user_time_zone)
    return local_time


def convert_to_masquerade_local(event_datetime, time_zone_str):
    """ Make a fake UTC time masquerade as local time - it will have the correct numeric time,  but needs 
     to have tzinfo UTC for flatpickr datetimes.  The user will interpret the datetime- correctly- as a datetime
     in their own time zone """

    local_time = convert_to_local(event_datetime, time_zone_str)
    # (Assuming local is EST, for example)  - Convert a "10:00 AM EST" time to "10:00 AM UTC."
    # The date in the form will technically be a false UTC.
    # (10:00 AM EST would really be 3 PM UTC the database)
    #  but the User will interpret the datetime as 10 AM EST
    utc_masquerade_local_time = local_time.replace(tzinfo=dt_timezone.utc)

    return utc_masquerade_local_time
