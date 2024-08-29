from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from tickets.models import Ticket  # , TicketHistory, transaction
from tickets.forms import TicketForm
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

        # If a staff user is requesting, get all forum threads.
        # otherwise, just get the threads
        # associated with a group the user is a part of.

        if is_admin:
            tickets = self.queryset.order_by('name')
        else:
            tickets = self.queryset.filter(
                author=self.request.user).order_by('name')

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
    template_name = 'create_post.html'

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
            form.instance.resolution_status = 'Open'
            ticket = form.save()
            return HttpResponseRedirect(reverse_lazy('tickets'))
            # return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': form.instance.pk}))
