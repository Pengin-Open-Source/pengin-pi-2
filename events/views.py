from django.contrib.auth.decorators import login_required
from django.shortcuts import render, reverse, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View

from .calendar import EventCalendar
from .forms import EventForm
from datetime import datetime

myCal = EventCalendar()


class CalendarMonth(View):
    template_name = "calendar/calendar_month.html"

    @method_decorator(login_required)
    def get(self, request, year=None, month=None):
        present_datetime = datetime.now()
        present_year = present_datetime.year
        present_month = present_datetime.month

        if year is None or month is None:
            year = present_year
            month = present_month

        calendar_html = myCal.formatmonth(int(year), int(month), withyear=True)

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


class CreateEvent(View):
    template_name = "calendar/create_event.html"

    @method_decorator(login_required)
    def get(self, request):
        return render(
            request,
            self.template_name,
            {
                "primary_title": "Create Event",
                "action": "create",
                "form": EventForm(),
            },
        )

    @method_decorator(login_required)
    def post(self, request):
        pass
