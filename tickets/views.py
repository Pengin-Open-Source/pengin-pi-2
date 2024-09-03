from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from tickets.models import Ticket, TicketComment, transaction, TicketHistory
from tickets.forms import TicketForm, TicketCommentForm
from util.security.auth_tools import group_required, is_admin_required
from django.utils import timezone


from main.models.users import User


class TicketsListView(LoginRequiredMixin, ListView):

    queryset = Ticket.objects.all()
    template_name = 'tickets.html'
    model = Ticket

    context_object_name = 'tickets'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_admin = self.request.user.is_authenticated and self.request.user.validated and self.request.user.is_staff
        context['is_admin'] = is_admin
        context['primary_title'] = 'Tickets'

        # If a staff user is requesting, get all tickets.
        # otherwise, just get the tickets authored
        # by the user

        if is_admin:
            tickets = self.queryset.order_by('date')
        else:
            tickets = self.queryset.filter(
                author=self.request.user).order_by('date')

        # Similar to what Sincere is using for companies
        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(tickets, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj

        return context


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketForm
    template_name = 'ticket_create.html'

    success_url = reverse_lazy('tickets')

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = TicketForm()
        context = {'form': form}
        return render(request, self.template_name,  context)

    def post(self, request):
        form = TicketForm(request.POST)
        if form.is_valid():
            form.instance.author = self.request.user
            form.instance.row_action = 'CREATE'
            form.instance.resolution_status = 'open'
            ticket = form.save()
            return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': ticket.pk}))


class TicketDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Ticket
    template_name = 'ticket.html'
    context_object_name = 'ticket'
    form_class = TicketForm

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # perhaps this should be refactored to use self.object instead?
        ticket = get_object_or_404(Ticket, id=self.kwargs.get('pk'))
        form = TicketForm(instance=ticket)
        for field in form.fields:
            form.fields[field].widget.attrs['disabled'] = True
        context['form'] = form

        # Get date ticket originally created, if available
        # and flag that tells you if it is not available
        if ticket.row_action == 'CREATE':
            ticket.is_create_missing = False
        else:
            ticket_creation_info = get_ticket_create_info(ticket)
            ticket.create_date, ticket.is_create_missing = ticket_creation_info

        comment_form = TicketCommentForm()
        comments = self.object.comments.all().order_by('-date')
        # for comment in comments:
        #     if comment.row_action == 'CREATE':
        #         comment.is_create_missing = False
        #         comment.author = comment.user.name
        #     else:
        #         comment_creation_info = get_comment_create_info(comment)
        #         comment_author_id, comment.create_date, comment.is_create_missing = comment_creation_info
        #         if comment_author_id != 'NOT FOUND':
        #             comment.author = User.objects.get(
        #                 id=comment_author_id).name
        #         else:
        #             comment.author = 'NOT FOUND'

        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(comments, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        context['comment_form'] = comment_form
        is_admin = self.request.user.is_authenticated and self.request.user.validated and self.request.user.is_staff
        context['is_admin'] = is_admin
        context['primary_title'] = self.object.summary
        return context

    def post(self, request, *args, **kwargs):
        ticket = self.get_object()
        comment_form = TicketCommentForm(request.POST)
        if comment_form.is_valid():
            comment_form.instance.ticket = ticket
            comment_form.instance.user = request.user
            comment_form.instance.row_action = 'CREATE'
            comment_form.save()
        return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': ticket.id}))

    def test_func(self):
        if self.request.user.is_authenticated and self.request.user.validated and self.request.user.is_staff:
            return True
        ticket = self.get_object()
        return self.request.user == ticket.author


class TicketEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ticket
    form_class = TicketForm
    template_name = 'ticket_edit.html'
    context_object_name = 'ticket'

    # def dispatch(self, request, *args, **kwargs):
    #     return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('ticket', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # perhaps should be refactored to use self.object?
        ticket = get_object_or_404(Ticket, id=self.kwargs.get('pk'))
        form = TicketForm(instance=ticket)
        context['form'] = form
        context['is_admin'] = self.request.user.is_staff
        context['primary_title'] = self.object.summary
        context['ticket_id'] = self.object.id
        return context

    def post(self, request, *args, **kwargs):
        ticket_id = self.kwargs.get('pk')
        ticket = get_object_or_404(
            Ticket, id=ticket_id)
        ticket_form = TicketForm(request.POST, instance=ticket)
        if ticket_form.is_valid():
            ticket = ticket_form.save(commit=False)
            ticket.last_edited_by = request.user
            ticket.row_action = 'EDIT'
            ticket.date = timezone.now()
            ticket.save()
            return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': ticket.id}))

    def test_func(self):
        is_validated_user = self.request.user.is_authenticated and self.request.user.validated
        if is_validated_user and self.request.user.is_staff:
            return True

        ticket = self.get_object()

        if ticket.row_action == 'CREATE':
            ticket.is_create_missing = False
        else:
            ticket_creation_info = get_ticket_create_info(ticket)
            ticket.create_date, ticket.is_create_missing = ticket_creation_info

        return is_validated_user and self.request.user == ticket.author and ticket.author != 'NOT FOUND'


class TicketDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ticket

    def post(self, request, *args, **kwargs):
        ticket = self.get_object()
        with transaction.atomic():
            delete_ticket(request.user, ticket)

        return HttpResponseRedirect(reverse_lazy('tickets'))

    def test_func(self):
        if self.request.user.is_authenticated and self.request.user.validated and self.request.user.is_staff:
            return True

        # ticket = self.get_object()
        # return self.request.user == ticket.author


def delete_ticket(usr, ticket):
    ticket.delete()


# class CommentEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
class TicketCommentEditView(LoginRequiredMixin, UpdateView):
    model = TicketComment
    form_class = TicketCommentForm
    template_name = 'comment_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # comment = get_object_or_404(
        # TicketComment, id = self.kwargs.get('pk'))
        # form = TicketCommentForm(instance=comment)
        # context['form'] = form
        context['is_admin'] = self.request.user.is_staff
        # context['thread_id'] = self.object.post.thread.id
        # context['post_id'] = self.object.post.id
        context['comment_id'] = self.object.id
        return context

        # def post(self, request, *args, **kwargs):
        #     comment_id = self.kwargs.get('pk')
        #     comment = get_object_or_404(
        #         ForumComment, id=comment_id)
        #     comment_form = ForumCommentForm(request.POST, instance=comment)
        #     if comment_form.is_valid():
        #         comment = comment_form.save(commit=False)
        #         comment.user = request.user
        #         comment.row_action = 'EDIT'
        #         comment.date = timezone.now()
        #         comment.save()
        #         return HttpResponseRedirect(reverse_lazy('post', kwargs={'thread_id': comment.post.thread_id,  'pk': comment.post.id}))

        # def test_func(self):
        #     comment = self.get_object()
        #     if comment.row_action == 'CREATE':
        #         comment_author = comment.user.name
        #     else:
        #         comment_creation_info = get_comment_create_info(comment)
        #         comment_author_id, comment.create_date, comment.is_create_missing = comment_creation_info
        #         if comment_author_id != 'NOT FOUND':
        #             comment_author = User.objects.get(id=comment_author_id).name
        #         else:
        #             comment_author = 'NOT FOUND'
        #     if self.request.user.is_staff:
        #         return True
        #     user_groups = self.request.user.groups.all()
        #     return comment.post.thread.groups.filter(id__in=user_groups).exists() and self.request.user.name == comment_author and comment_author != 'NOT FOUND'


# Used to get original date/author of an edited ticket
def get_ticket_create_info(ticket):
    oldest_date = ''
    is_create_missing = False

    ticket_history = TicketHistory.objects.filter(
        ticket_id=ticket.id,  row_action="CREATE")

    # there should be only one value.
    # we will set a flag if there is no row with method 'CREATE'  in ForumPostHistory
    oldest_ticket_record = ticket_history.first()

    if oldest_ticket_record:
        oldest_date = oldest_ticket_record.date
    else:
        # DBAs TAKE NOTE: If a DBA deletes some older Forum Post History Records
        # then the row with the ForumPost's initial creation date/original author could have
        # been deleted and unavailable now!
        is_create_missing = True
        oldest_date = 'DATE NOT FOUND'
    return (oldest_date, is_create_missing)
