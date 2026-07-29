# tickets/urls.py
from django.urls import path
from tickets.views import (
    TicketSettings, TicketsFilterView, TicketCreateView, TicketDetailView, TicketDeleteView,
    TicketCommentEditView, TicketEditView, TicketCommentDeleteView, TicketEditStatusView,
    RequesterOfTicketPendingReopenRequestsView, HandlerOfResolvedTicketReopenRequestsView, HandlerOfResolvedTicketReopenRequestDetailView,
    HandlerOfPendingTicketReopenRequestDetailView, RequesterOfTicketReopenRequestDetailView, ApproveTicketReopenRequestView,
    DenyTicketReopenRequestView, RequesterOfResolvedTicketReopenRequestsView, RequesterOfResolvedTicketReopenRequestDetailView
)

urlpatterns = [
    path('', TicketsFilterView.as_view(), name='tickets'),
    path('<status>', TicketsFilterView.as_view(), name='tickets'),
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
         RequesterOfTicketPendingReopenRequestsView.as_view(), name='view_pending_reopen_requests'),
    path('<uuid:pk>/view-all-resolved-reopen-requests/<str:status>/',
         HandlerOfResolvedTicketReopenRequestsView.as_view(), name='view_all_resolved_reopen_requests'),
    path('<uuid:pk>/view-resolved-reopen-requests-for-specific-user/<str:status>/',
         RequesterOfResolvedTicketReopenRequestsView.as_view(), name='view_resolved_reopen_requests_for_specific_user'),
    path('<uuid:pk>/view-pending-reopen-request-details/',
         HandlerOfPendingTicketReopenRequestDetailView.as_view(), name='view_pending_request_details'),
    path('<uuid:pk>/view-my-pending-request/',
         RequesterOfTicketReopenRequestDetailView.as_view(), name='view_my_pending_request'),
    path('<uuid:pk>/view-extended-resolved-request-details/',
         HandlerOfResolvedTicketReopenRequestDetailView.as_view(), name='view_extended_resolved_request_details'),
    path('<uuid:pk>/view-resolved-request-details-for-specific-user/',
         RequesterOfResolvedTicketReopenRequestDetailView.as_view(), name='view_resolved_request_details_for_specific_user'),
    path('<uuid:pk>/approve-reopen-request/',
         ApproveTicketReopenRequestView.as_view(), name='approve_reopen_request'),
    path('<uuid:pk>/deny-reopen-request/',
         DenyTicketReopenRequestView.as_view(), name='deny_reopen_request'),


]
