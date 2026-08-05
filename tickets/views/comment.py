# Edit and Delete User comments (Creation of Comments currently on Ticket Detail View)
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DeleteView, UpdateView

from main.mixins import LoginAndValidationRequiredMixin
from tickets.forms import TicketCommentForm
from tickets.models import Ticket, TicketComment, transaction
from tickets.permissions import can_comment_on_ticket, is_ticket_manager
from tickets.views.util import delete_comment


class TicketCommentEditView(LoginAndValidationRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TicketComment
    form_class = TicketCommentForm
    template_name = 'comment_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comment = get_object_or_404(
            TicketComment, id=self.kwargs.get('pk'))
        form = TicketCommentForm(instance=comment)
        context['form'] = form
        context['is_admin'] = self.request.user.is_staff
        context['ticket_id'] = self.object.ticket.id
        context['comment_id'] = self.object.id
        return context

    def post(self, request, *args, **kwargs):
        comment_id = self.kwargs.get('pk')
        comment = get_object_or_404(TicketComment, id=comment_id)
        comment_form = TicketCommentForm(request.POST, instance=comment)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.last_edited_by = request.user
            comment.row_action = 'EDIT'
            comment.date = timezone.now()
            comment.save()
            return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': comment.ticket.id}))

    def test_func(self):
        current_user = self.request.user
        if current_user.is_staff:
            return True

        comment = self.get_object()
        ticket = get_object_or_404(Ticket, id=comment.ticket.id)
        if is_ticket_manager(current_user, ticket):
            return True
        if can_comment_on_ticket(current_user, ticket) and current_user == comment.author:
            return True


class TicketCommentDeleteView(LoginAndValidationRequiredMixin, UserPassesTestMixin, DeleteView):
    model = TicketComment

    def post(self, request, *args, **kwargs):
        archive_comment = self.get_object()
        ticket_id = archive_comment.ticket.id
        with transaction.atomic():
            delete_comment(request.user, archive_comment)
        return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': ticket_id}))

    def test_func(self):
        current_user = self.request.user
        if current_user.is_staff:
            return True

        comment = self.get_object()
        ticket = get_object_or_404(Ticket, id=comment.ticket.id)
        if is_ticket_manager(current_user, ticket):
            return True
        if can_comment_on_ticket(current_user, ticket) and current_user == comment.author:
            return True

        return False
