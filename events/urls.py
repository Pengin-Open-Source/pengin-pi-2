from django.urls import path
from .views import CalendarMonth

# Add namespace to urls
app_name = 'calendar'

urlpatterns = [
    path('', CalendarMonth.as_view(), name='calendar'),
    path('<int:year>/<int:month>/', CalendarMonth.as_view(), name='calendar_month'),
]