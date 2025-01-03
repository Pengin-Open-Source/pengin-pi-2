from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render, reverse, get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from main.mixins import LoginAndValidationRequiredMixin
from .models import Event

from .calendar import EventCalendar
from .forms import EventForm, CalendarSettingsForm
from .permissions import can_create_or_see_event, can_change_event
from datetime import datetime


myCal = EventCalendar()


class CalendarMonth(LoginAndValidationRequiredMixin, View):
    template_name = "calendar/calendar_month.html"

    def get(self, request, year=None, month=None):
        present_datetime = datetime.now()
        present_year = present_datetime.year
        present_month = present_datetime.month

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
            form.instance.author = request.user
            form.instance.row_action = 'CREATE'
            event = form.save()

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

        form = EventForm(instance=event)
        form_rendered_for_edit = form.render(
            "configure_event_form.html")
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
            event.date = timezone.now()
            event.row_action = 'EDIT'
            event.save()
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
