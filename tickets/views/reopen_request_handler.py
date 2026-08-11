# Ticket Reopen Requests.
# From the perspective of any user who can Grant or Deny the request
# View Request details, Grant or Deny Requests, see past Resolved Requests.
# NOTE For now,  Ticket Reopen Requests *creation* happens on the Ticket Detail View

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView, UpdateView

from main.mixins import LoginAndValidationRequiredMixin

from tickets.models import Ticket, TicketOpenRequest, transaction

from tickets.forms import (
    HandlerOfResolvedTicketOpenRequestForm,
    TicketOpenRequestResponseForm,
    TicketPendingOpenRequestForm,
)

from tickets.permissions import (
    can_approve_reopen_requests_for_ticket,
    can_approve_this_reopen_request
)


class HandlerOfPendingTicketReopenRequestsView(LoginAndValidationRequiredMixin,  UserPassesTestMixin, DetailView):
    template_name = 'reopen_requests_pending.html'
    model = Ticket
    context_object_name = 'ticket'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        requested_ticket = get_object_or_404(Ticket, id=self.kwargs.get('pk'))
        context['primary_title'] = 'Pending Requests to Open Ticket #' + \
            str(requested_ticket.ticket_number) + \
            ": " + requested_ticket.summary

        requests = TicketOpenRequest.objects.filter(ticket=requested_ticket).filter(
            approval_status="pending").order_by('-request_date')

        # Similar to what Sincere is using for companies
        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(requests, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj

        return context

    def test_func(self):
        current_user = self.request.user
        ticket = self.get_object()
        return can_approve_reopen_requests_for_ticket(current_user, ticket)


class HandlerOfPendingTicketReopenRequestDetailView(LoginAndValidationRequiredMixin, UserPassesTestMixin, DetailView):
    template_name = "handler_pending_reopen_request.html"
    model = TicketOpenRequest
    form_class = TicketPendingOpenRequestForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reopen_request = get_object_or_404(
            TicketOpenRequest, id=self.kwargs.get('pk'))
        requested_ticket = reopen_request.ticket
        form = TicketPendingOpenRequestForm(instance=reopen_request)

        for field in form.fields:
            form.fields[field].widget.attrs['disabled'] = True
        context['form'] = form

        context["reopen_request"] = reopen_request
        context["ticket_id"] = requested_ticket.id
        context["primary_title"] = "Request to Reopen Ticket #" + \
            str(requested_ticket.ticket_number) + \
            ": " + requested_ticket.summary

        return context

    def test_func(self):
        current_user = self.request.user
        reopen_request = self.get_object()
        return can_approve_this_reopen_request(current_user, reopen_request)


class ApproveTicketReopenRequestView(LoginAndValidationRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TicketOpenRequest
    form_class = TicketOpenRequestResponseForm
    template_name = 'reopen_request_approve.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reopen_request = get_object_or_404(
            TicketOpenRequest, id=self.kwargs.get('pk'))
        form = TicketOpenRequestResponseForm(instance=reopen_request)
        context['form'] = form
        context["reopen_request"] = reopen_request
        context['ticket_id'] = self.object.ticket.id
        context['request_id'] = self.object.id
        context["primary_title"] = "Approve Reopen of Ticket #" + str(self.object.ticket.ticket_number) + ": " + \
            self.object.ticket.summary
        return context

    def post(self, request, *args, **kwargs):
        approved_request = get_object_or_404(
            TicketOpenRequest, id=self.kwargs.get('pk'))
        ticket = approved_request.ticket
        approved_request_form = TicketOpenRequestResponseForm(
            request.POST, instance=approved_request)
        if approved_request_form.is_valid():
            # The following tasks must succeed or fail together,
            # so I'm using a transaction:
            # 1) Approve this request directly
            # 2) Reopen the ticket
            # 3) Update any other *pending* requests to reopen
            #    this ticket and indicate that another request
            #    was approved.

            with transaction.atomic():
                # approve this request directly

                approved_request = approved_request_form.save(commit=False)
                approved_request.approval_status = 'approved'
                approved_request.reviewer = request.user
                approved_request.date_handled = timezone.now()
                approved_request.row_action = 'EDIT'
                approved_request.save()
                # open the ticket if it's not open.
                if ticket.resolution_status != 'open':
                    ticket.last_edited_by = request.user
                    ticket.owner = approved_request.author
                    ticket.row_action = 'EDIT'
                    ticket.date = timezone.now()
                    ticket.resolution_status = 'open'
                    ticket.resolution_date = None
                    ticket.save()
                # indirectly resolve any other reopen requests on this ticket
                other_pending = TicketOpenRequest.objects.filter(
                    # very pendantic FYI :-) : ticket_id is the db field - not ORM - name,
                    # and its actually cheaper to use.
                    approval_status='pending').filter(ticket_id=ticket.id)
                other_pending_ids = list(
                    other_pending.values_list('pk', flat=True))
                for pending_request_id in other_pending_ids:
                    pending_request = TicketOpenRequest.objects.get(
                        pk=pending_request_id)
                    pending_request.approval_status = 'related request approved'

                    # Uncomment this??? I'm inclined not to - since this request
                    # wasn't DIRECTLY approved. The reviewer of the approved request
                    # may never have even read the other requests' reasons for
                    # reopening. However, he/she did indirectly approve, so there's
                    # two ways to look at it.
                    # approved_request.reviewer = request.user

                    pending_request.date_handled = timezone.now()
                    pending_request.row_action = 'EDIT'
                    # link back to the request that caused this one to be resolved
                    pending_request.related_request_approved = approved_request
                    pending_request.save()

            return HttpResponseRedirect(reverse_lazy('view_pending_reopen_requests', kwargs={'pk': ticket.id}))

    def test_func(self):
        current_user = self.request.user
        reopen_request = self.get_object()
        return can_approve_this_reopen_request(current_user, reopen_request)


class DenyTicketReopenRequestView(LoginAndValidationRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TicketOpenRequest
    form_class = TicketOpenRequestResponseForm
    template_name = 'reopen_request_deny.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reopen_request = get_object_or_404(
            TicketOpenRequest, id=self.kwargs.get('pk'))
        form = TicketOpenRequestResponseForm(instance=reopen_request)
        context['form'] = form
        context["reopen_request"] = reopen_request
        context['ticket_id'] = self.object.ticket.id
        context['request_id'] = self.object.id
        context["primary_title"] = "Deny Reopen of Ticket #" + str(self.object.ticket.ticket_number) + ": " + \
            self.object.ticket.summary
        return context

    def post(self, request, *args, **kwargs):
        denied_request = get_object_or_404(
            TicketOpenRequest, id=self.kwargs.get('pk'))
        ticket = denied_request.ticket
        denied_request_form = TicketOpenRequestResponseForm(
            request.POST, instance=denied_request)
        if denied_request_form.is_valid():
            denied_request = denied_request_form.save(commit=False)
            denied_request.approval_status = 'denied'
            denied_request.reviewer = request.user
            denied_request.date_handled = timezone.now()
            denied_request.row_action = 'EDIT'
            denied_request.save()
            return HttpResponseRedirect(reverse_lazy('view_pending_reopen_requests', kwargs={'pk': ticket.id}))

    def test_func(self):
        current_user = self.request.user
        reopen_request = self.get_object()
        return can_approve_this_reopen_request(current_user, reopen_request)


class HandlerOfResolvedTicketReopenRequestsView(LoginAndValidationRequiredMixin,  UserPassesTestMixin, DetailView):
    template_name = 'all_resolved_reopen_requests.html'
    model = Ticket
    context_object_name = 'ticket'

    def get_context_data(self, **kwargs):
        status = self.kwargs.get('status')

        # circumvent pending status being used here.
        if status is None or status.lower() == 'pending':
            status = 'all'
        status = status.lower()

        context = super().get_context_data(**kwargs)
        requested_ticket = get_object_or_404(Ticket, id=self.kwargs.get('pk'))
        context['primary_title'] = 'Resolved Requests to Open Ticket #' + \
            str(requested_ticket.ticket_number) + \
            ": " + requested_ticket.summary

        # Currently treating everything not pending as resolved
        # Not currently excluding anything created with the error status,
        # in the name of letting such errors bubble up to the surface
        # TODO - figure out how to handle OpenRequests with Error status
        # in the GUI
        if status == 'all':
            # all means "all handled requests" in this context. ALWAYS exclude pending.
            requests = TicketOpenRequest.objects.filter(ticket=requested_ticket).exclude(
                approval_status="pending").order_by('-date_handled')
        else:
            requests = TicketOpenRequest.objects.filter(ticket=requested_ticket).filter(
                approval_status=status).order_by('-date_handled')

            # Similar to what Sincere is using for companies
        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(requests, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj

        return context

    def test_func(self):
        current_user = self.request.user
        ticket = self.get_object()
        return can_approve_reopen_requests_for_ticket(current_user, ticket)


class HandlerOfResolvedTicketReopenRequestDetailView(LoginAndValidationRequiredMixin, UserPassesTestMixin, DetailView):
    template_name = "past_reopen_request.html"
    model = TicketOpenRequest

    form_class = HandlerOfResolvedTicketOpenRequestForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reopen_request = get_object_or_404(
            TicketOpenRequest, id=self.kwargs.get('pk'))
        requested_ticket = reopen_request.ticket
        form = HandlerOfResolvedTicketOpenRequestForm(instance=reopen_request)

        for field in form.fields:
            form.fields[field].widget.attrs['disabled'] = True
        context['form'] = form
        context['is_handler'] = True
        context["reopen_request"] = reopen_request
        context["ticket_id"] = requested_ticket.id
        context["primary_title"] = "RESOLVED Request to Reopen Ticket #" + \
            str(requested_ticket.ticket_number) + \
            ": " + requested_ticket.summary

        return context

    def test_func(self):
        current_user = self.request.user
        reopen_request = self.get_object()
        return can_approve_reopen_requests_for_ticket(current_user, reopen_request.ticket)
