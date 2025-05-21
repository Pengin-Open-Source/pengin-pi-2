from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from main.models.users import User
from tickets.models import Ticket, TicketComment, transaction, TicketHistory, TicketCommentHistory
from tickets.forms import TicketForm, TicketCommentForm, TicketEditStatusForm
from main.mixins import LoginAndValidationRequiredMixin
from tickets.permissions import can_see_ticket, can_edit_ticket, is_ticket_manager
from util.security.group_access import can_access_group, get_users_with_extended_rbac_to_group,  get_all_groups_for_user_with_extended_rbac,  get_group_managers, is_manager_of_this_role


class TicketsListView(LoginAndValidationRequiredMixin, ListView):

    queryset = Ticket.objects.all()
    template_name = 'tickets.html'
    model = Ticket

    context_object_name = 'tickets'

    def get_context_data(self, **kwargs):
        status = self.kwargs.get('status')
        if status is None:
            status = 'all'
        context = super().get_context_data(**kwargs)
        is_admin = self.request.user.is_staff
        context['is_admin'] = is_admin
        context['primary_title'] = 'Tickets'

        # If a staff user is requesting, get all tickets.
        # Otherwise, get the tickets this particular user has
        # permission to see

        if status != 'all':
            if is_admin:
                tickets = self.queryset.filter(
                    resolution_status=status).order_by('-date')
            else:
                tickets = Ticket.objects.filter(
                    resolution_status=status).filter_by_can_see_ticket(
                    self.request.user).order_by('-date')
        else:
            if is_admin:
                tickets = self.queryset.order_by('-date').order_by('-date')
            else:
                tickets = Ticket.objects.filter_by_can_see_ticket(
                    self.request.user).order_by('-date')

        for ticket in tickets:
            if ticket.row_action == 'CREATE':
                ticket.is_create_missing = False
            else:
                ticket_creation_info = get_ticket_create_info(ticket)
                ticket.create_date, ticket.is_create_missing = ticket_creation_info

        # Similar to what Sincere is using for companies
        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(tickets, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj

        return context


class TicketCreateView(LoginAndValidationRequiredMixin, CreateView):
    model = Ticket
    form_class = TicketForm
    template_name = 'ticket_create.html'

    success_url = reverse_lazy('tickets')

    def get(self, request, *args, **kwargs):

        # this is the group that that a new Ticket's Role field will be set
        # to by default.  This will be the only option available for
        # users with no roles and no special privileges to create their
        # tickets in. group_created is just to catch the unused T/F result.
        default_role, group_created = Group.objects.get_or_create(
            name='default_ticket_support')
        all_groups = Group.objects.all()

        # Does this user manage ANY role/group?
        group_managers = get_group_managers()
        users_who_manage = User.objects.filter(id__in=group_managers)

        is_a_role_manager = self.request.user in users_who_manage

        # If I'm staff or a manager,  I can change the ticket to any role
        # and my preloaded owner options are any users who are in
        # the default role (if any,  otherwise we get an empty select list)
        if self.request.user.is_staff or is_a_role_manager:

            role_options = all_groups
            owner_options = get_users_with_extended_rbac_to_group(default_role)
        else:
            # If I am not a staff or a manager,  I may not assign the
            # ticket to any *user* to be the Ticket Owner
            # (calling this with no role returns an empty list of users)
            owner_options = get_users_with_extended_rbac_to_group()
            # ..but I can assign the ticket to any *role* I have access to
            user_roles = get_all_groups_for_user_with_extended_rbac(
                self.request.user)
            if user_roles.exists():
                # Get all the roles the user is connected with
                # + the default_ticket_support role
                role_options = user_roles | Group.objects.filter(
                    pk=default_role.pk)
            else:
                # If I am not connected with any role,  I must assign the ticket
                # to default ticket support,  leaving management to assign it
                # to the correct role and owner later in the Edit Ticket page.
                role_options = Group.objects.filter(pk=default_role.pk)

        form = TicketForm(role_options=role_options,
                          owner_options=owner_options, role_default=default_role)
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
        role_options = Group.objects.filter(pk=default_role.pk)
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

        comment_form = TicketCommentForm()
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
        context['comment_form'] = comment_form
        is_admin = self.request.user.is_staff
        context['is_admin'] = is_admin
        context['can_edit_ticket'] = can_edit_ticket(self.request.user, ticket)
        context['primary_title'] = self.object.summary + \
            " | Status: " + self.object.resolution_status.upper()
        return context

    def post(self, request, *args, **kwargs):
        ticket = self.get_object()
        comment_form = TicketCommentForm(request.POST)
        if comment_form.is_valid():
            comment_form.instance.ticket = ticket
            comment_form.instance.author = request.user
            comment_form.instance.row_action = 'CREATE'
            comment_form.save()
        return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': ticket.id}))

    def test_func(self):
        return can_see_ticket(self.request.user, self.get_object())


class TicketEditView(LoginAndValidationRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ticket
    form_class = TicketForm
    template_name = 'ticket_edit.html'
    context_object_name = 'ticket'

    # Google Gemini suggested using the dispatch function
    # to check for AJAX call to give back a JSONResponse
    def dispatch(self, request, *args, **kwargs):
        selected_role = request.GET.get('selected_role')
        current_user = self.request.user
        if selected_role:
            # It's an Ajax request, handle it differently
            the_role_object = get_object_or_404(Group, id=selected_role)

            # permission flag: May the User see the option to set Owner to empty?
            can_set_ticket_owner_blank = False

            ticket = get_object_or_404(Ticket, id=self.kwargs.get('pk'))
            ticket_owner = None

            if ticket.owner:
                ticket_owner = get_object_or_404(User, id=ticket.owner.id)
            else:
                can_set_ticket_owner_blank = True

            if current_user.is_staff or is_manager_of_this_role(current_user, the_role_object):
                potential_owners_for_the_role = get_users_with_extended_rbac_to_group(
                    the_role_object)
                can_set_ticket_owner_blank = True

            else:
                if (can_access_group(current_user, the_role_object.id)):
                    # The user can assign themselves as Owner.
                    # If the ticket has an owner, and that owner has access
                    # to the newly selected_role,  they can see that as well
                    if can_access_group(ticket_owner, the_role_object.id):
                        potential_owners_for_the_role = User.objects.filter(
                            id=current_user.id) | User.objects.filter(
                            id=ticket_owner.id)
                    else:
                        potential_owners_for_the_role = User.objects.filter(
                            id=current_user.id)
                else:
                    # user cannot:
                    # 1) See any role but default_ticket_support
                    # 2) assign Ownership to anyone
                    # user CAN
                    # can see the current owner, if there is one
                    if ticket_owner:
                        potential_owners_for_the_role = ticket_owner
                    else:  # just show the default (empty) owner list
                        potential_owners_for_the_role = get_users_with_extended_rbac_to_group()

            owner_options = []
            if can_set_ticket_owner_blank:
                owner_options.append({'value': "",  'label': "---------"})

            for user in potential_owners_for_the_role:
                owner_options.append(
                    {'value': user.pk,  'label': str(user.name)})

            data = {'message': f'Newly Selected Role: {selected_role}',
                    'status': 'success',  'options': owner_options}
            return JsonResponse(data)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('ticket', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # perhaps should be refactored to use self.object?
        ticket = get_object_or_404(Ticket, id=self.kwargs.get('pk'))
        # For existing tickets,  the default role is the currently
        # saved Ticket Role
        default_role = ticket.role
        all_groups = Group.objects.all()

        # Does this user manage ANY role/group?
        group_managers = get_group_managers()
        users_who_manage = User.objects.filter(id__in=group_managers)

        is_a_role_manager = self.request.user in users_who_manage
        users_in_default_role = get_users_with_extended_rbac_to_group(
            default_role)
        current_user_has_default_role = self.request.user in users_in_default_role
        # Setting this here, because it is both a value and a flag.
        # Determines if the "no owner" option is available to the user
        ticket_owner = None
        # If I'm staff or a manager,  I can change the ticket to any role
        # and my preloaded owner options are any users who are in
        # the default role (if any,  otherwise we get an empty select list)
        if self.request.user.is_staff or is_a_role_manager:
            role_options = all_groups
            # TODO restrict option for non-staff managers to the roles they manage
            owner_options = users_in_default_role
        else:
            if ticket.owner:
                ticket_owner = User.objects.filter(id=ticket.owner.id)

            # If I am not a staff or a manager,  I may not assign the
            # ticket to any *OTHER user* to be the Ticket Owner..
            # ..but I can assign the ticket to any *role* I have access to
            user_roles = get_all_groups_for_user_with_extended_rbac(
                self.request.user)
            if user_roles.exists():
                # Get all the roles the user is connected with
                # + the default_ticket_support role
                role_options = user_roles | Group.objects.filter(
                    pk=default_role.pk)
                # Since the user is part of these roles, they can assign
                # the ticket to themself -unless the current role is default_ticket_support,
                # and the user is not part of that role. They can also see the ticket owner, if
                # there is one
                if default_role.name != "default_ticket_support" or current_user_has_default_role:
                    owner_options = User.objects.filter(
                        id=self.request.user.id) | ticket_owner
                else:
                    if ticket_owner:
                        owner_options = ticket_owner
                    else:  # just show the default (empty) owner list
                        owner_options = get_users_with_extended_rbac_to_group()

            else:
                # If I am not connected with any role,  I must leave the ticket
                # in default ticket support,  and I may not assign to anyone else,
                # ... but I can see the current owner, if there is one
                role_options = Group.objects.filter(pk=default_role.pk)
                if ticket_owner:
                    owner_options = ticket_owner
                else:  # just show the default (empty) owner list
                    owner_options = get_users_with_extended_rbac_to_group()

        # Note that Owner_default = NONE EITHER means: 1) The Ticket has no owner
        # or 2) The user is a Group Manager or Staff member,  who has permission
        # to make an assigned Ticket "Unassigned" again.  (or both)
        form = TicketForm(role_options=role_options, owner_options=owner_options,
                          role_default=default_role, owner_default=ticket_owner, instance=ticket)

        context['form'] = form
        context['is_admin'] = self.request.user.is_staff
        context['primary_title'] = self.object.summary
        context['ticket_id'] = self.object.id
        return context

    # def get(self, request, **kwargs):
    #     context = self.get_context_data(**kwargs)
    #     return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        ticket_id = self.kwargs.get('pk')
        ticket = get_object_or_404(
            Ticket, id=ticket_id)
        ticket_form = TicketForm(request.POST, instance=ticket)
        if ticket_form.is_valid():
            # ticket = ticket_form.save(commit=False)
            ticket_to_be_edited = ticket_form.instance
            ticket_to_be_edited.last_edited_by = request.user
            ticket_to_be_edited.row_action = 'EDIT'
            ticket_to_be_edited.date = timezone.now()
            ticket_form.instance = ticket_to_be_edited
            ticket = ticket_form.save()
            return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': ticket.id}))

    def test_func(self):

        ticket = self.get_object()
        return can_edit_ticket(self.request.user, ticket)


class TicketEditStatusView(LoginAndValidationRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ticket
    form_class = TicketEditStatusForm
    template_name = 'ticket_edit_status.html'
    context_object_name = 'ticket'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # perhaps should be refactored to use self.object?
        ticket = get_object_or_404(Ticket, id=self.kwargs.get('pk'))
        form = TicketEditStatusForm(instance=ticket)
        context['form'] = form
        context['is_admin'] = self.request.user.is_staff
        context['primary_title'] = self.object.summary
        context['ticket_id'] = self.object.id
        return context

    def post(self, request, *args, **kwargs):
        ticket_id = self.kwargs.get('pk')
        ticket = get_object_or_404(
            Ticket, id=ticket_id)
        ticket_form = TicketEditStatusForm(request.POST, instance=ticket)
        if ticket_form.is_valid():
            ticket = ticket_form.save(commit=False)
            ticket.last_edited_by = request.user
            ticket.row_action = 'EDIT'
            ticket.date = timezone.now()
            if ticket.resolution_status == 'resolved':
                ticket.resolution_date = timezone.now()
            else:
                ticket.resolution_date = ''

            ticket.save()
            return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': ticket.id}))

    def test_func(self):
        if self.request.user.is_staff:
            return True

        ticket = self.get_object()

        return self.request.user == ticket.author


class TicketDeleteView(LoginAndValidationRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ticket

    def post(self, request, *args, **kwargs):
        ticket = self.get_object()
        delete_ticket(request.user, ticket)

        return HttpResponseRedirect(reverse_lazy('tickets'))

    def test_func(self):
        if self.request.user.is_staff:
            return True


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
        if self.request.user.is_staff:
            return True

        comment = self.get_object()

        return self.request.user == comment.author


class TicketCommentDeleteView(LoginAndValidationRequiredMixin, UserPassesTestMixin, DeleteView):
    model = TicketComment

    def post(self, request, *args, **kwargs):
        archive_comment = self.get_object()
        ticket_id = archive_comment.ticket.id
        with transaction.atomic():
            delete_comment(request.user, archive_comment)
        return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': ticket_id}))

    def test_func(self):
        if self.request.user.is_staff:
            return True

        comment = self.get_object()

        # TODO  Perhaps customer-level users shouldn'te  be allowed to delete STAFF comments
        # Also,  should managers be allowed to delete comments?

        return self.request.user == comment.author


##                   ##
#   UTILITY METHODS
##                   ##


# Used to get original date of an edited ticket


def get_ticket_create_info(ticket):
    oldest_date = ''
    is_create_missing = False

    ticket_history = TicketHistory.objects.filter(
        ticket_id=ticket.id,  row_action="CREATE")

    # there should be only one value.
    # we will set a flag if there is no row with method 'CREATE'  in TicketHistory
    oldest_ticket_record = ticket_history.first()

    if oldest_ticket_record:
        oldest_date = oldest_ticket_record.date
    else:
        # DBAs TAKE NOTE: If a DBA deletes some older Ticket History Records
        # then the row with the Ticket's initial creation date could have
        # been deleted and unavailable now!
        is_create_missing = True
        oldest_date = 'DATE NOT FOUND'
    return (oldest_date, is_create_missing)


# Since this method can have multiple operations that must succeed or fail together,
# I'm putting a transaction at the top of this method.
def delete_ticket(usr, archive_ticket):
    with transaction.atomic():
        archive_ticket.row_action = 'DELETE'
        archive_ticket.last_edited_by = usr
        archive_ticket.date = timezone.now()

        # First,  try to delete all the comments
        # If any deletion fails down the chain,  the whole deletion
        # process should be canceled.
        comments = archive_ticket.comments.all().order_by('-date')
        for comment in comments:
            delete_comment(usr, comment)

        # specify this is an deleted record
        # both save and delete must execute or fail together,
        # this keeps track of the time of deletion and
        # the user who deleted the record
        archive_ticket.save()
        archive_ticket.delete()
        return "success"


# Used to get original date/author of an edited comment
def get_comment_create_info(comment):
    oldest_date = ''
    is_create_missing = False

    comment_history = TicketCommentHistory.objects.filter(
        comment_id=comment.id,  row_action="CREATE")

    # there should be only one value.
    # we will set a flag if there is no row with method 'CREATE'  in Comment History
    oldest_comment_record = comment_history.first()
    if oldest_comment_record:
        oldest_date = oldest_comment_record.date
    else:
        # DBAs TAKE NOTE: If a DBA deletes some older Ticket Comment history records,
        # then the row with the TicketComment's initial creation date could have
        # been deleted and unavailable now!
        is_create_missing = True
        oldest_date = 'DATE NOT FOUND'
    return (oldest_date, is_create_missing)


# Not putting a transaction at the top of this method itself,  b/c
# this method may be called inside of the delete_ticket method.
# I want failures to propagate up the chain and rollback the whole
# ticket deletion, and not leave a deletion in a half-done state
def delete_comment(usr, archive_comment):

    archive_comment.row_action = 'DELETE'
    archive_comment.last_edited_by = usr
    archive_comment.date = timezone.now()

    # specify this is an deleted record
    # both save and delete must execute or fail together,
    # this keeps track of the time of deletion and
    # the user who deleted the record
    archive_comment.save()
    archive_comment.delete()

    # Uncomment to test error in a transaction after both operations complete successfully
    # if "Comment about widgets" in archive_comment.content:
    #   raise TestTransactionError("Test Delete Comment Failure.")
    return "success"
