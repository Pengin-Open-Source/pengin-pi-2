from datetime import datetime, date
from django.shortcuts import reverse
import calendar

from events.models import Event


class EventCalendar(calendar.HTMLCalendar):
    def __init__(self):
        self.month_events = {}
        self.year = None
        self.month = None
        super(EventCalendar, self).__init__()

    def get_event_html(self, events):
        events_html = ""
        if events:
            events_html = "<div class='calendar-day-events'><ul class='events-list'>"
            for event in events:
                event_url = reverse("calendar:detail-event", kwargs={"event_id": event.id})
                events_html += (
                    f"<li class='calendar-day-event'>"
                    f"<a href='{event_url}' class='event-link'>"
                    f"<span class='event-start-time'>{event.start_time}</span>"
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

        events_in_month = Event.objects.all()
        # events_in_month=Event.objects.filter(
        #     Event.start_datetime < datetime(year, month, 1) + relativedelta(months=1),
        #     Event.end_datetime >= datetime(year, month, 1),
        # ).order_by(Event.start_datetime)

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
