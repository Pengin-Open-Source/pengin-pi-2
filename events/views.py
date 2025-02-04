from zoneinfo import ZoneInfo
# Have to specify package for "timezone" b/c I'm importing two differant timezones
from datetime import datetime, timezone as dt_timezone
from django.utils import timezone as dj_util_timezone
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render, reverse, get_object_or_404, redirect
from django.views import View
from django.db import transaction
from main.mixins import LoginAndValidationRequiredMixin
from .models import Event, EventParticipant, EventHistory

from .calendar import EventCalendar
from .forms import EventForm, CalendarSettingsForm
from .permissions import can_create_or_see_event, can_change_event

# Credit to Google Gemini for some coding assistence in this file.

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

        # Get date the event was originally created, if that is available,
        # along with the flag that tells you if it is available
        if event.row_action == 'CREATE':
            event.is_create_missing = False
            event.create_date = event.date
        else:
            event_creation_info = get_event_create_info(event)
            event.create_date, event.is_create_missing = event_creation_info
            event.last_edit_date = event.date

        return render(
            request,
            self.template_name,
            {
                "primary_title": event.title,
                "event": event,
                "can_change": can_change_event(request, event_id),
            },
        )


class CreateEvent(LoginAndValidationRequiredMixin, UserPassesTestMixin, View):
    model = Event
    form_class = EventForm
    template_name = "calendar/event_form.html"

    def test_func(self):
        return can_create_or_see_event(self.request, self.kwargs.get("event_id"))

    def get(self, request, *args, **kwargs):
        if "event_id" in self.kwargs:
            initial = self.get_initial()
            form = EventForm(initial)
            user_time_zone_str = self.request.COOKIES.get('time_zone')
            initial["start_datetime"] = convert_to_masquerade_local(
                initial.get("start_datetime"), user_time_zone_str)
            initial["end_datetime"] = convert_to_masquerade_local(
                initial.get("end_datetime"), user_time_zone_str)
            primary_title = "Duplicate Event: " + initial.get("title")
        else:
            form = EventForm()
            primary_title = "Create Event"

        form_rendered_for_create = form.render(
            "configure_event_form.html")
        context = {
            "primary_title": primary_title,
            "action": "create",
            "form": form_rendered_for_create,

        }
        return render(request, self.template_name, context)

    def get_initial(self):
        event = get_object_or_404(Event, id=self.kwargs["event_id"])
        current_participants_ids = EventParticipant.objects.filter(
            event_id=event.id).values_list('participant_id', flat=True)
        event_roles = event.roles.all().values_list('id', flat=True)

        return {
            "title": event.title,
            "description": event.description,
            "location": event.location,
            "organizer": event.organizer,
            "participants": current_participants_ids,
            "roles":  event_roles,
            "start_datetime": event.start_datetime,
            "end_datetime": event.end_datetime,
        }

    def post(self, request, **kwargs):
        form = EventForm(request.POST)
        if form.is_valid():
            event_to_be_saved = form.instance
            # event = form.save(commit=False)
            event_to_be_saved.author = request.user
            event_to_be_saved.row_action = 'CREATE'

            # See EditEvent's post method for details
            user_time_zone_str = request.COOKIES.get('time_zone')
            event_to_be_saved.start_datetime = convert_to_utc(
                event_to_be_saved.start_datetime, user_time_zone_str)
            event_to_be_saved.end_datetime = convert_to_utc(
                event_to_be_saved.end_datetime, user_time_zone_str)

            # event.save()
            form.instance = event_to_be_saved
            event = form.save()

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
            # for some reason,  editing the event after a form.save doesn't allow me
            # to save event roles, so now I assign an event placeholder to the form instance
            # make changes,  then set form.instance = the event placeholder, then do
            # form.save().  Now it lets roles be updated.
            # event = form.save(commit=False)
            event_to_be_edited = form.instance
            event_to_be_edited.last_edited_by = request.user
            event_to_be_edited.row_action = 'EDIT'
            event_to_be_edited.date = dj_util_timezone.now()

            # Working with Google's AI and also referring to Flask version for this)
            # - Grab the timezone that was stored as a cookie in layout.html,  convert
            # the time into the correct UTC time.
            # The reason we are converting a date that is already utc into utc,
            # is because the user THINKS they entered the date time in their own timezone.
            # We need to do some tweaks to get the transformation right.
            user_time_zone_str = request.COOKIES.get('time_zone')
            event_to_be_edited.start_datetime = convert_to_utc(
                event_to_be_edited.start_datetime, user_time_zone_str)
            event_to_be_edited.end_datetime = convert_to_utc(
                event_to_be_edited.end_datetime, user_time_zone_str)
            form.instance = event_to_be_edited

            attendees_to_delete = EventParticipant.objects.filter(
                participant_id__in=form.delete_participants, event_id=event.id)
            # If we're supposed to add or delete participants but we can't,
            # roll back the whole event edit.
            with transaction.atomic():
                event = form.save()
                for attendee in form.participants_to_add:
                    EventParticipant.objects.create(
                        event=event, added_by=request.user, participant=attendee,  row_action='CREATE')

                for not_attending in attendees_to_delete:
                    delete_participant(request.user, not_attending)

            return redirect("calendar:detail-event", event_id=event.id)

        context = self.get_context_data()
        form_rendered_for_edit = form.render("configure_event_form.html")
        context["form"] = form_rendered_for_edit

        error_list = []
        for field, errors in form.errors.items():
            if field == '__all__':
                error_list.append("Warning! Errors were found:")
            else:
                error_list.append(f"Errors for field '{field}':")
            for error in errors:
                error_list.append(f"- {error}")
        context["form_errors"] = error_list
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
        delete_event(request.user, event)
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

    ###########  DATETIME CONVERSION METHODS ########

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
     to have tzinfo UTC for flatpickr datetimes.  The user will mentally interpret the datetime- correctly- as a datetime
     in their own time zone """

    # TODO - For visually impaired customers,  find out if screen readers will state the timezone to the user-
    # - or if they will simply say the datetime.  If the latter,  then a blind user will likely interpret
    # the datetime the same as a sighted user would. If the former,  we will either need to scrap this workaround
    # or add in some kind of screen reader tags to notify the blind user of the real timezone

    local_time = convert_to_local(event_datetime, time_zone_str)
    # (Assuming local is EST, for example)  - Convert a "10:00 AM EST" time to "10:00 AM UTC."
    # The date in the form will technically be a false UTC.
    # (10:00 AM EST would really be 3 PM UTC the database)
    #  but the User will interpret the datetime as 10 AM EST
    utc_masquerade_local_time = local_time.replace(tzinfo=dt_timezone.utc)

    return utc_masquerade_local_time

    ###########  Deletion and Record Creation Information Methods ########


# Used to get original date of an edited event
def get_event_create_info(event):
    oldest_date = ''
    is_create_missing = False

    event_history = EventHistory.objects.filter(
        event_id=event.id,  row_action="CREATE")

    # there should be only one value.
    # we will set a flag if there is no row with method 'CREATE'  in TicketHistory
    oldest_event_record = event_history.first()

    if oldest_event_record:
        oldest_date = oldest_event_record.date
    else:
        # DBAs TAKE NOTE: If a DBA deletes some older Event History Records
        # then the row with the Event's initial creation date could have
        # been deleted and unavailable now!
        is_create_missing = True
        oldest_date = 'DATE NOT FOUND'
    return (oldest_date, is_create_missing)


# Since this method can have multiple operations that must succeed or fail together,
# I'm putting a transaction at the top of this method.
def delete_event(usr, archive_event):
    with transaction.atomic():
        archive_event.row_action = 'DELETE'
        archive_event.last_edited_by = usr
        archive_event.date = dj_util_timezone.now()

        # First, try to delete all the Event Participants.
        # If any deletion fails down the chain,  the whole deletion
        # process should be canceled.
        # FYI, I think this reverse date ordering is important for deleting in a for-loop
        event_participants = archive_event.participants.all().order_by('-date')
        for event_particpant in event_participants:
            delete_participant(usr, event_particpant)

        # specify this is an deleted record
        # both save and delete must execute or fail together,
        # this keeps track of the time of deletion and
        # the user who deleted the record
        archive_event.save()
        archive_event.delete()
        return "success"


# Since this method will be called WITHIN a transaction, we will NOT
# put a transaction at the top
def delete_participant(usr, event_participant):

    event_participant.row_action = 'DELETE'
    event_participant.deleted_by = usr
    event_participant.date = dj_util_timezone.now()
    event_participant.save()
    event_participant.delete()
    return "success"
