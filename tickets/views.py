from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from tickets.models import Ticket, TicketComment, transaction  # , TicketHistory,
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
            form.instance.user = self.request.user
            form.instance.row_action = 'CREATE'
            form.instance.resolution_status = 'open'
            ticket = form.save()
            return HttpResponseRedirect(reverse_lazy('tickets'))
            # return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': form.instance.pk}))


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

        # if forum_post.row_action == 'CREATE':
        #     post_author = forum_post.user.name
        #     forum_post.is_create_missing = False
        # else:
        #     post_creation_info = get_post_create_info(forum_post)
        #     post_author_id, forum_post.create_date, forum_post.is_create_missing = post_creation_info
        #     if post_author_id != 'NOT FOUND':
        #         post_author = User.objects.get(id=post_author_id).name
        #     else:
        #         post_author = 'NOT FOUND'

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
        ticket = self.get_object()
        is_admin = self.request.user.is_authenticated and self.request.user.validated and self.request.user.is_staff
        if is_admin:
            return True
        else:
            return self.request.user == ticket.author


class TicketDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ticket

    def post(self, request, *args, **kwargs):
        ticket = self.get_object()

        with transaction.atomic():
            delete_ticket(request.user, ticket)

        return HttpResponseRedirect(reverse_lazy('tickets'))

    def test_func(self):
        ticket = self.get_object()
        is_admin = self.request.user.is_authenticated and self.request.user.validated and self.request.user.is_staff
        if is_admin:
            return True
        return self.request.user == ticket.author


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
