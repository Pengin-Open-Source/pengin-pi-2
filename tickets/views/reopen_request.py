# Ticket Reopen Requests
# From the perspective of the user who made the request
# View Pending Request details, also  see past Resolved Requests.
# NOTE For now,  Ticket Reopen Requests *creation* happens on the Ticket Detail View

class RequesterOfTicketReopenRequestDetailView(LoginAndValidationRequiredMixin, UserPassesTestMixin, DetailView):

    # Pending Reopen request for a specific ticket from the current user. There is no "list page" for this,
    # for this view,  since the rule is a user may not have more than one pending reopen request
    # per ticket. They must wait for the current pending request to be handled; then they can make
    # a new request as needed.

    template_name = "my_pending_reopen_request.html"
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
        context["primary_title"] = "My Request to Reopen Ticket #: " + \
            str(requested_ticket.ticket_number) + \
            ": " + requested_ticket.summary

        return context

    def test_func(self):
        current_user = self.request.user
        reopen_request = self.get_object()
        if reopen_request.author == current_user and is_reopen_request_pending_approval(reopen_request) and can_see_ticket(current_user, reopen_request.ticket):
            return True
        return False


class RequesterOfResolvedTicketReopenRequestsView(LoginAndValidationRequiredMixin,  UserPassesTestMixin, DetailView):
    template_name = 'my_resolved_reopen_requests.html'
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
        context['primary_title'] = self.request.user.name + "'s Resolved Requests to Open Ticket #" + \
            str(requested_ticket.ticket_number) + \
            ": " + requested_ticket.summary

        # Currently treating everything not pending as resolved
        # Not currently excluding anything created with the error status,
        # in the name of letting such errors bubble up to the surface
        # TODO - figure out how to handle OpenRequests with Error status
        # in the GUI
        if status == 'all':
            # all means "all handled requests" in this context. ALWAYS exclude pending.
            requests = TicketOpenRequest.objects.filter(ticket=requested_ticket).filter(
                author=self.request.user).exclude(approval_status="pending").order_by('-date_handled')
        else:
            requests = TicketOpenRequest.objects.filter(ticket=requested_ticket).filter(
                author=self.request.user).filter(approval_status=status).order_by('-date_handled')
        context["ticket_id"] = requested_ticket.id
        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(requests, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj

        return context

    def test_func(self):
        current_user = self.request.user
        ticket = self.get_object()
        # even if a user has requests, they can't see them when their access is revoked
        if not can_see_ticket(current_user, ticket):
            return False
        user_resolved_requests = TicketOpenRequest.objects.filter(
            ticket=ticket).filter(author=current_user).exclude(approval_status="pending")

        return user_resolved_requests.exists()


class RequesterOfResolvedTicketReopenRequestDetailView(LoginAndValidationRequiredMixin, UserPassesTestMixin, DetailView):
    # Notice how we use the same template for both Specific Users
    # viewing their own requests, & Ticket Reopen Request Reviewers
    # looking at ANY of this Ticket's past reopen requests.
    template_name = "past_reopen_request.html"
    model = TicketOpenRequest

    form_class = RequesterOfResolvedTicketOpenRequestForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reopen_request = get_object_or_404(
            TicketOpenRequest, id=self.kwargs.get('pk'))
        requested_ticket = reopen_request.ticket
        form = SpecificUserResolvedTicketOpenRequestForm(
            instance=reopen_request)

        for field in form.fields:
            form.fields[field].widget.attrs['disabled'] = True
        context['form'] = form

        context["reopen_request"] = reopen_request
        context["ticket_id"] = requested_ticket.id
        context["primary_title"] = self.request.user.name + "'s RESOLVED Request to Reopen Ticket #" + \
            str(requested_ticket.ticket_number) + \
            ": " + requested_ticket.summary

        return context

    def test_func(self):
        current_user = self.request.user
        reopen_request = self.get_object()
        if not can_see_ticket(current_user, reopen_request.ticket):
            return False
        return reopen_request.author == current_user
