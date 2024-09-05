# tickets/urls.py
from django.urls import path
from tickets.views import (
    TicketsListView, TicketCreateView, TicketDetailView, TicketDeleteView,  TicketCommentEditView, TicketEditView, TicketCommentDeleteView
)

urlpatterns = [
    path('', TicketsListView.as_view(), name='tickets'),
    path('create/', TicketCreateView.as_view(), name='create_ticket'),
    path('<uuid:pk>/', TicketDetailView.as_view(), name='ticket'),
    path('<uuid:pk>/edit/',
         TicketEditView.as_view(), name='edit_ticket'),
    path('<uuid:ticket_id>/<uuid:pk>/edit/',
         TicketCommentEditView.as_view(), name='edit_ticket_comment'),
    path('delete/Ticket/<uuid:pk>/',
         TicketDeleteView.as_view(), name='delete_ticket'),
    path('delete/comment/<uuid:pk>/',
         TicketCommentDeleteView.as_view(), name='delete_ticket_comment'),
]
