from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView
from django_filters.views import FilterView

from main.mixins import LoginAndValidationRequiredMixin
from main.models.users import User
from tickets.filters import FilterSortOrder, TicketFilter
from tickets.forms import (
    TicketCommentForm,
    TicketCreateOpenRequestForm,
    TicketForm
)
from tickets.models import (
    Ticket,
    TicketOpenRequest,
    transaction
)
from tickets.permissions import (
    can_approve_reopen_requests_for_ticket,
    can_comment_on_ticket,
    can_edit_ticket,
    can_edit_ticket_status,
    can_request_reopen,
    can_see_ticket
)
from util.security.group_access import (
    get_users_with_extended_rbac_to_group,
    is_manager_of_this_role,
)

from tickets.views.util import get_ticket_create_info, get_comment_create_info


class TicketsFilterView(LoginAndValidationRequiredMixin, FilterView):

    # queryset = Ticket.objects.all()
    template_name = 'tickets.html'
    model = Ticket
    filterset_class = TicketFilter
    context_object_name = 'tickets'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tickets = self.object_list
        context['sort_order_filter_form'] = FilterSortOrder(
            self.request.GET, queryset=self.object_list).form
        # User-chosen sort order - or default to most recent activity 1st.
        sort_by = self.request.GET.get('sort_order', '-last_activity')
        tickets = tickets.order_by(sort_by)

        for ticket in tickets:
            if ticket.row_action == 'CREATE':
                ticket.is_create_missing = False
            else:
                ticket_creation_info = get_ticket_create_info(ticket)
                ticket.create_date, ticket.is_create_missing = ticket_creation_info

        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(tickets, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj

        page_range_with_ellipsis = paginator.get_elided_page_range(
            page_obj.number, on_each_side=2, on_ends=1)

        context['page_range_with_ellipsis'] = page_range_with_ellipsis

        # Preserve any search parameters the user chose,
        # when we have moved to a new page in paginated results
        # get rid of any prior page selection from query parameters
        # This takes the current GET params and allows us to swap 'page' easily
        query = self.request.GET.copy()
        if 'page' in query:
            del query['page']
        context['query_parameters'] = query.urlencode()

        is_admin = self.request.user.is_staff
        context['is_admin'] = is_admin

        # Using a session variable to keep track of whether this user can see all
        # validated users in the Ticket Owner dropdown list
        show_all_users = self.request.session.get(
            'owner_displays_all_validated_users')
        if show_all_users is None:
            show_all_users = False
        # here is where a change can take place....
        show_all_users = show_all_users and is_admin
        self.request.session['owner_displays_all_validated_users'] = show_all_users

        # Look for errors in the Selected Filter Criteria
        filterset = self.filterset
        context['primary_title'] = 'Tickets'
        # Check if the filter form has been submitted and has errors
        if filterset.is_bound and not filterset.is_valid():
            error_list = []
            for field, errors in filterset.errors.items():
                if field == '__all__':
                    error_list.append("Warning! Errors were found:")
                else:
                    error_list.append(f"Errors for field '{field}':")

                for error in errors:
                    error_list.append(f"- {error}")

            context["form_errors"] = error_list

        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.kwargs.get('status', 'all')

        is_admin = self.request.user.is_staff

        # If a staff user is requesting, get all tickets.
        # Otherwise, get the tickets this particular user has
        # permission to see

        if status != 'all':
            if is_admin:
                tickets = queryset.filter(
                    resolution_status=status)
            else:
                tickets = Ticket.objects.filter(
                    resolution_status=status).filter_by_can_see_ticket(
                    self.request.user)
        else:
            if is_admin:
                tickets = queryset
            else:
                tickets = Ticket.objects.filter_by_can_see_ticket(
                    self.request.user)

        return tickets.annotate(last_activity=F('ticketlatestactivity__latest_activity')).order_by('-last_activity')


class TicketDetailView(LoginAndValidationRequiredMixin, UserPassesTestMixin, DetailView):
    model = Ticket
    template_name = 'ticket.html'
    context_object_name = 'ticket'
    form_class = TicketForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # perhaps this should be refactored to use self.object instead?
        ticket = get_object_or_404(Ticket, id=self.kwargs.get('pk'))
        default_role = ticket.role
        manages_ticket = is_manager_of_this_role(
            self.request.user, default_role)
        role_options = Group.objects.filter(pk=default_role.pk)

        # Only the ticket.owner should be visible: don't want the other users
        # to even be frontend code; that way users can't snoop with developer
        # tools to see all the users they don't have permission to see.
        if ticket.owner:
            owner_options = User.objects.filter(id=ticket.owner.id)
        else:  # this should return an empty queryset of Users
            owner_options = get_users_with_extended_rbac_to_group()

        form = TicketForm(role_options=role_options, owner_options=owner_options, owner_default=ticket.owner,
                          instance=ticket)
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

        #### HANDLE COMENTS #######

        # don't allow comments if user can't edit the ticket
        can_comment = can_comment_on_ticket(self.request.user, ticket)
        context['can_comment'] = can_comment
        if can_comment:
            comment_form = TicketCommentForm()
            context['comment_form'] = comment_form

        comments = self.object.comments.all().order_by('-date')
        for comment in comments:
            if comment.row_action == 'CREATE':
                comment.is_create_missing = False
            else:
                comment_creation_info = get_comment_create_info(comment)
                comment.create_date, comment.is_create_missing = comment_creation_info

        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(comments, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj

        ##########  HANDLE REOPEN TICKET REQUESTS ##############
        context['has_pending_requests_for_me_to_approve'] = False
        context['has_made_pending_requests'] = False
        context['user_has_resolved_requests'] = False
        context["can_ask_to_reopen"] = False
        context["can_approve_reopen_request"] = False

        resolved_requests = TicketOpenRequest.objects.filter(
            ticket=ticket).exclude(approval_status="pending")
        ticket_has_resolved_requests = resolved_requests.exists()
        context['ticket_has_resolved_requests'] = ticket_has_resolved_requests
        if can_approve_reopen_requests_for_ticket(self.request.user, ticket):
            pending_requests = TicketOpenRequest.objects.filter(ticket=ticket).filter(
                approval_status="pending")
            context["can_approve_reopen_request"] = True
            context['has_pending_requests_for_me_to_approve'] = pending_requests.exists()
        elif can_request_reopen(self.request.user, ticket):
            # Get Request Reopen Form for this user
            reopen_request_form = TicketCreateOpenRequestForm()
            context['reopen_request_form'] = reopen_request_form
            context["can_ask_to_reopen"] = True

            # if there are resolved requests,  find out if any were from this user
            if ticket_has_resolved_requests:
                resolved_requests_from_user = resolved_requests.filter(
                    author=self.request.user).exclude(approval_status="pending")
                context['user_has_resolved_requests'] = resolved_requests_from_user.exists()
        else:
            # get this user's pending request
            my_pending_requests = TicketOpenRequest.objects.filter(ticket=ticket).filter(
                approval_status="pending").filter(author=self.request.user)
            # this should always be true if we get to this point in the code
            context['has_made_pending_requests'] = my_pending_requests.exists()
            context['reopen_request'] = my_pending_requests.first()

            # if there are resolved requests,  find out if any were from this user
            if ticket_has_resolved_requests:
                resolved_requests_from_user = resolved_requests.filter(
                    author=self.request.user).exclude(approval_status="pending")
                context['user_has_resolved_requests'] = resolved_requests_from_user.exists()
        ##########################################################

        context['is_ticket_manager'] = manages_ticket
        is_admin = self.request.user.is_staff
        context['is_admin'] = is_admin
        context['can_edit_ticket'] = can_edit_ticket(self.request.user, ticket)
        context['can_edit_ticket_status'] = can_edit_ticket_status(
            self.request.user, ticket)
        context['primary_title'] = "Ticket #" + str(ticket.ticket_number) + ": " + self.object.summary + \
            " |  Submitted by: " + self.object.author.name + \
            " | Status: " + self.object.resolution_status.upper()
        return context

    def post(self, request, *args, **kwargs):
        ticket = self.get_object()
        # don't allow comments if user can't edit the ticket
        if can_comment_on_ticket(self.request.user, ticket):
            comment_form = TicketCommentForm(request.POST)
            if comment_form.is_valid():
                comment_form.instance.ticket = ticket
                comment_form.instance.author = request.user
                comment_form.instance.row_action = 'CREATE'
                comment_form.save()
                # If a comment is being made by an author, on a closed ticket, automatically reopen!
                if ticket.resolution_status == 'closed' and ticket.author == request.user:
                    ticket.last_edited_by = request.user
                    ticket.row_action = 'EDIT'
                    ticket.date = timezone.now()
                    ticket.resolution_status = 'open'
                    ticket.resolution_date = None
                    reopen_requests_pending = ticket.reopen_requests.filter(
                        approval_status='pending')
                    if reopen_requests_pending.exists():
                        with transaction.atomic():
                            # we indirectly resolved reopen requests on this ticket
                            reopen_requests_pending = ticket.reopen_requests.filter(
                                approval_status='pending')
                            reopen_requests_pending_ids = list(
                                reopen_requests_pending.values_list('pk', flat=True))
                            for pending_request_id in reopen_requests_pending_ids:
                                pending_request = TicketOpenRequest.objects.get(
                                    pk=pending_request_id)
                                pending_request.approval_status = 'manually reopened'

                                pending_request.date_handled = timezone.now()
                                pending_request.row_action = 'EDIT'
                                # link back to the request that caused this one to be resolved
                                pending_request.bypass_initiated_by = request.user
                                pending_request.save()
                            ticket.save()
                    else:
                        ticket.save()

        elif can_request_reopen(self.request.user, ticket):
            reopen_form = TicketCreateOpenRequestForm(request.POST)
            if reopen_form.is_valid():
                reopen_form.instance.ticket = ticket
                reopen_form.instance.author = request.user
                reopen_form.instance.row_action = 'CREATE'
                reopen_form.save()
        return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': ticket.id}))

    def test_func(self):
        return can_see_ticket(self.request.user, self.get_object())
