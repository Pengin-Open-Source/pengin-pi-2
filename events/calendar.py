from datetime import datetime, date
from zoneinfo import ZoneInfo
from django.db.models import Q
from django.shortcuts import reverse
import calendar
from .permissions import can_create_or_see_all_event_details, can_see_public_event, is_month_too_far_away

from events.models import Event


class EventCalendar(calendar.HTMLCalendar):
    def __init__(self):
        self.month_events = {}
        self.year = None
        self.month = None
        self.user_time_zone = None
        self.user_settings = False
        super(EventCalendar, self).__init__()

    def get_event_html(self, events):
        events_html = ""
        if events:
            events_html = "<div class='calendar-day-events'><ul class='events-list'>"
            for event in events:
                event_url = reverse("calendar:detail-event",
                                    kwargs={"event_id": event.id})
                events_html += (
                    f"<li class='calendar-day-event'>"
                    f"<a href='{event_url}' class='event-link'>"
                    f"<span class='event-start-time'>{
                        event.start_time()}</span>"
                    f" - "
                    f"<span class='event-title'>{event.title}</span>"
                    f"</a></li>"
                )
            events_html += "</ul></div>"
        return events_html

    # def formatweek(self, theweek):
    #     """
    #     Return a complete week as a table row.
    #     """
    #     s = "".join(self.formatday(d, wd) for (d, wd) in theweek)
    #     return '<tr class="calendar-week">%s</tr>' % s

    def set_time_zone(self, time_zone_str):
        self.user_time_zone = ZoneInfo(time_zone_str)
        return None

    def formatday(self, day, weekday):
        try:
            events_from_day = self.month_events[self.year][self.month].get(day)
        except KeyError:
            events_from_day = ""
        return self.day_cell(weekday, day, events=events_from_day)

    def day_cell(self, weekday, day, events=""):
        if day == 0:
            return "<td class='noday calendar-day--not-current'>&nbsp;</td>"  # day outside month
        else:
            supp_classes = "calendar-day"
            if date(self.year, self.month, day) == date.today():
                supp_classes += " calendar-day--today"
            events_html = self.get_event_html(events)
            cell_html = (
                f"<td class='{self.cssclasses[weekday]} {supp_classes}'>"
                f"<div class='calendar-day-of-month'>{day}</div>"
                f"{events_html}</td>"
            )
            return cell_html

    def formatmonth(self, year, month, *args, **kwargs):

        # To handle year and month-end edge cases,
        # the year and month passed in from the view
        # will be from the local timezone
        self.year = year
        self.month = month
        self.cssclass_month += " calendar-month"
        self.month_events = {}
        current_user = kwargs.pop("current_user")

        # Get a copy of all events in the user's local timezone before
        # displaying the calendar. Events at 8 PM Dec 31, 2025 should
        # show up in December's calendar for New York users,  and in
        # January's calendar month for London users

        # To manage this with UTC database times and local front-end
        # times,  we get the local beginning and ending midnights
        # of this month
        month_start = get_local_time_beginning_of_month_in_utc(
            year, month, self.user_time_zone)

        if month < 12:
            next_month = month + 1
            next_month_year = year
        else:
            next_month = 1
            next_month_year = year + 1
        month_end = get_local_time_beginning_of_month_in_utc(
            next_month_year, next_month, self.user_time_zone)
        print("Month End")
        print(month_end)
        print("Month Start")
        print(month_start)
        time_conditions = Q(start_datetime__gte=month_start, start_datetime__lt=month_end) | Q(
            end_datetime__gte=month_start, end_datetime__lt=month_end) | Q(start_datetime__lt=month_start, end_datetime__gte=month_end)

        # Regardless of other filters, get only the events this month.
        events_local_time_zone = Event.objects.filter(time_conditions)

        # notice these are two differant data structures - one's a list and can't use order_by
        # I don't *think* this will make a difference for the loop picking out the events.
        if current_user.is_staff:
            events_in_month = events_local_time_zone.order_by("start_datetime")
        else:
            events_in_month = filter_events(
                events_local_time_zone, year, month, current_user)

        for day in self.itermonthdays(year, month):
            if day > 0:
                day_date = datetime(year, month, day).date()
                day_events = (
                    self.month_events.setdefault(year, {})
                    .setdefault(month, {})
                    .setdefault(day, [])
                )

                for event in events_in_month:
                    # Moving this conversion here, after we have filtered 
                    # down WHICH events we need in this month
                    event.start_datetime = event.start_datetime.astimezone(
                        self.user_time_zone)
                    event.end_datetime = event.end_datetime.astimezone(
                        self.user_time_zone)

                    # Check if event is happening during day and not already saved
                    if (
                        event.start_date() <= day_date <= event.end_date()
                        and event not in day_events
                    ):
                        day_events.append(event)

        return super(EventCalendar, self).formatmonth(year, month, *args, **kwargs)

################ UTILITY METHODS #############################
## Gemini's suggestion for replacing filter(Q....)#########
# def filter_objects(objects, conditions):
#     filtered_objects = []
#     for obj in objects:
#         if all(condition(obj) for condition in conditions):
#             filtered_objects.append(obj)
#     return filtered_objects

# ETA. Show public events also


def filter_events(events, year, month, current_user=None):
    filtered_events = []

    if is_month_too_far_away(year, month):
        # don't look for public events
        for event in events:
            if can_create_or_see_all_event_details(current_user, event.id):
                filtered_events.append(event)
    else:
        # include public events
        for event in events:
            if (can_see_public_event(event) or can_create_or_see_all_event_details(current_user, event.id)):
                filtered_events.append(event)

    return filtered_events


# Slight tweak of Gemini's solution for getting the UTC equivalent of whatever
# time the user's "local midnight" of the first day of the month is.
# Since Event dates are stored as UTC,  but displayed as local times,
# getting a month's dates to display in LOCAL time requires
# care when dealing with the beginning/end of months
def get_local_time_beginning_of_month_in_utc(year: int, month: int, user_time_zone: ZoneInfo) -> datetime:
    """
    Returns a datetime object representing midnight (00:00:00) on the 
    first day of the specified month and year, converted to UTC.

    Args:
        year (int): The calendar year (e.g., 2026).
        month (int): The calendar month (1 for January, 12 for December).
        time_zone_str (str): The string identifier for the local time zone 
                             (e.g., 'America/New_York').

    Returns:
        datetime: A timezone-aware datetime object in UTC.
    """

    # 1. Define UTC time zone
    utc_zone = ZoneInfo('UTC')

    # 2. Create a naive datetime object for the first day at midnight
    naive_dt = datetime(year, month, 1, 0, 0, 0)

    # 3. Localize the naive datetime object (Local Midnight)
    local_midnight_dt = naive_dt.replace(tzinfo=user_time_zone)

    # 4. Convert the local time to UTC
    # The .astimezone() method handles the shift based on the time zone info.
    utc_dt = local_midnight_dt.astimezone(utc_zone)

    return utc_dt
