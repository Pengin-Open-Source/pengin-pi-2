from django.urls import path
from .views import CalendarMonth, CreateEvent, DetailEvent

# Add namespace to urls
app_name = 'calendar'

urlpatterns = [
    path('', CalendarMonth.as_view(), name='calendar'),
    path('<int:year>/<int:month>/', CalendarMonth.as_view(), name='calendar-month'),
    path('create_event/', CreateEvent.as_view(), name='create-event'),
    path('<uuid:event_id>/', DetailEvent.as_view(), name='detail-event'),
]