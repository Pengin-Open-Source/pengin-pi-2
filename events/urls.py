from django.urls import path
from .views import CalendarMonth, CreateEvent, DetailEvent, EditEvent, DeleteEvent

# Add namespace to urls
app_name = 'calendar'

urlpatterns = [
    path('', CalendarMonth.as_view(), name='calendar'),
    path('<int:year>/<int:month>/', CalendarMonth.as_view(), name='calendar-month'),
    path('create_event/', CreateEvent.as_view(), name='create-event'),
    path('<uuid:event_id>/', DetailEvent.as_view(), name='detail-event'),
    path('<uuid:event_id>/copy/', CreateEvent.as_view(), name='copy-event'),
    path('<uuid:event_id>/edit/', EditEvent.as_view(), name='edit-event'),
    path('<uuid:event_id>/delete/', DeleteEvent.as_view(), name='delete-event'),
]