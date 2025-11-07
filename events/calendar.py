from datetime import datetime, date
from zoneinfo import ZoneInfo
# from django.db.models import Q
from django.shortcuts import reverse
import calendar
from .permissions import can_create_or_see_all_event_details, can_see_public_event

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
        self.year = year
        self.month = month
        self.cssclass_month += " calendar-month"
        self.month_events = {}
        current_user = kwargs.pop("current_user")

        # Get a copy of all events in the user's local timezone before
        # displaying the calendar. Events at 8 PM Dec 31, 2025 should
        # show up in December's calendar for New York users,  and in
        # January's calendar month for London users
        events_local_time_zone = Event.objects.all()
        for event in events_local_time_zone:
            event.start_datetime = event.start_datetime.astimezone(
                self.user_time_zone)
            event.end_datetime = event.end_datetime.astimezone(
                self.user_time_zone)
        # CANNOT USE ANYMORE.  I am changing in-memory objects (to use local time),
        # and filter apparently filters on the original (UTC) values in the database
        # if current_user.is_staff:
        #     events_in_month = events_local_time_zone.filter(
        #         # Filter events that are happening during the month
        #         Q(start_datetime__year=year, start_datetime__month=month)
        #         | Q(end_datetime__year=year, end_datetime__month=month)
        #     ).order_by("start_datetime")
        # else:
        #     events_in_month = events_local_time_zone.filter(
        #         # Filter events that are happening during the month
        #         Q(start_datetime__year=year, start_datetime__month=month)
        #         | Q(end_datetime__year=year, end_datetime__month=month),
        #         # Filter events that current user is involved in
        #         Q(author=current_user)
        #         | Q(organizer=current_user)
        #         | Q(participants=current_user)
        #     ).order_by("start_datetime")

        # GEMINI's suggestion to replace the filter with Q
        # conditions = [
        #     lambda obj: obj.field1 > 10,
        #     lambda obj: obj.other_field == 'some_value'
        # ]
        # filtered_objects = filter_objects(objects, conditions)

        conditions = [

            lambda event: event.start_datetime.year == year and event.start_datetime.month == month,
            # Event Starts during this month
            lambda event: event.start_datetime.year == year and event.start_datetime.month == month,
            # Event Ends during this month
            lambda event: event.end_datetime.year == year and event.end_datetime.month == month,

            lambda event: ((event.start_datetime.year == year and event.start_datetime.month < month)
                           or
                           # event started before this month
                           (event.start_datetime.year < year))
            and
                          ((event.end_datetime.year == year and event.end_datetime.month > month)
                              or
                              # event ends after this month
                              (event.end_datetime.year > year)
                           )
        ]
        events_in_month = filter_events(
            events_local_time_zone, conditions, current_user)

        for day in self.itermonthdays(year, month):
            if day > 0:
                day_date = datetime(year, month, day).date()
                day_events = (
                    self.month_events.setdefault(year, {})
                    .setdefault(month, {})
                    .setdefault(day, [])
                )
                for event in events_in_month:
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


def filter_events(events, conditions, current_user=None):
    filtered_events = []
    if conditions == []:
        for event in events:
            if can_see_public_event(event):
                filtered_events.append(event)

    for event in events:
        if any(condition(event) for condition in conditions) and (can_see_public_event(event) or can_create_or_see_all_event_details(current_user, event.id)):
            filtered_events.append(event)

    return filtered_events
