# View for Ticket Status Changes

class TicketEditStatusView(LoginAndValidationRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ticket
    form_class = TicketEditStatusForm
    template_name = 'ticket_edit_status.html'
    context_object_name = 'ticket'

    # Gemini's suggestion for how to fix a bug occuring on an implicit form
    # load,  that happens before the form call in get_context_data method
    # I want current_user for permission checks to filter the available
    # statuses.

    def get_form_kwargs(self):
        """
        Injects the 'current_user' argument into the form's __init__ method
        before the form is instantiated.
        """
        # Get the standard kwargs (instance, data, initial, etc.)
        kwargs = super().get_form_kwargs()

        # Add the custom argument that your form's __init__ needs
        kwargs['current_user'] = self.request.user

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # perhaps should be refactored to use self.object?
        ticket = get_object_or_404(Ticket, id=self.kwargs.get('pk'))
        current_user = self.request.user
        form = TicketEditStatusForm(instance=ticket, current_user=current_user)
        context['form'] = form
        context['is_admin'] = self.request.user.is_staff
        context['primary_title'] = "Edit Status for Ticket #" + \
            str(self.object.ticket_number) + ": " + self.object.summary
        context['ticket_id'] = self.object.id
        return context

    def post(self, request, *args, **kwargs):
        ticket_id = self.kwargs.get('pk')
        ticket = get_object_or_404(
            Ticket, id=ticket_id)
        current_user = self.request.user
        ticket_form = TicketEditStatusForm(
            request.POST, instance=ticket, current_user=current_user)
        # what was the resolution status and date before now?
        if ticket.resolution_status == 'open':
            resolve_date = None
        else:
            # grab the resolution date that existed before this
            # post
            resolve_date = ticket.resolution_date
        if ticket_form.is_valid():
            # now ticket object contains the newly selected status
            ticket = ticket_form.save(commit=False)
            ticket.last_edited_by = request.user
            ticket.row_action = 'EDIT'
            ticket.date = timezone.now()
            reopen_requests_pending = None
            handle_requests = False
            if ticket.resolution_status == 'resolved' and not ticket.resolution_date:
                ticket.resolution_date = timezone.now()
            # if we are CHANGING the status to open, blank out the date.
            elif ticket.resolution_status == 'open':
                ticket.resolution_date = None
                reopen_requests_pending = ticket.reopen_requests.filter(
                    approval_status='pending')
                if reopen_requests_pending.exists():
                    handle_requests = True
                # bypass_initiated_by
            # otherwise just keep the current resolution date.
            else:
                ticket.resolution_date = resolve_date

            if handle_requests:
                with transaction.atomic():
                    # we indirectly resolved reopen requests on this ticket
                    reopen_requests_pending_ids = list(
                        reopen_requests_pending.values_list('pk', flat=True))
                    for pending_request_id in reopen_requests_pending_ids:
                        pending_request = TicketOpenRequest.objects.get(
                            pk=pending_request_id)
                        pending_request.approval_status = 'manually reopened'

                        pending_request.date_handled = timezone.now()
                        pending_request.row_action = 'EDIT'
                        # link back to the request that caused this one to be resolved
                        pending_request.bypass_initiated_by = current_user
                        pending_request.save()
                        ticket.save()
            else:
                ticket.save()
            return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': ticket.id}))

    def test_func(self):
        current_user = self.request.user
        ticket = self.get_object()
        if can_edit_ticket_status(current_user, ticket):
            return True
        return False
