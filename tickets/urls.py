# tickets/urls.py
from django.urls import path
from tickets.views import (
    TicketSettings, TicketsListView, TicketCreateView, TicketDetailView, TicketDeleteView,
    TicketCommentEditView, TicketEditView, TicketCommentDeleteView, TicketEditStatusView,
    TicketPendingReopenRequestsView, TicketReopenRequestDetails
)

urlpatterns = [
    path('', TicketsListView.as_view(), name='tickets'),
    path('<status>', TicketsListView.as_view(), name='tickets'),
    path('create/', TicketCreateView.as_view(), name='create_ticket'),
    path('<uuid:pk>/', TicketDetailView.as_view(), name='ticket'),
    path('<uuid:pk>/edit/',
         TicketEditView.as_view(), name='edit_ticket'),
    path('<uuid:pk>/edit-status/',
         TicketEditStatusView.as_view(), name='edit_ticket_status'),
    path('ticket-settings/', TicketSettings.as_view(), name='ticket_settings'),
    path('<uuid:ticket_id>/<uuid:pk>/edit/',
         TicketCommentEditView.as_view(), name='edit_ticket_comment'),
    path('delete/ticket/<uuid:pk>/',
         TicketDeleteView.as_view(), name='delete_ticket'),
    path('delete/comment/<uuid:pk>/',
         TicketCommentDeleteView.as_view(), name='delete_ticket_comment'),
    path('<uuid:pk>/view-pending-reopen-requests/',
         TicketPendingReopenRequestsView.as_view(), name='view_pending_reopen_requests'),
    path('<uuid:pk>/view-pending-reopen-request_details/',
         TicketReopenRequestDetails.as_view(), name='view_pending_request_details'),

]
