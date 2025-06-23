from django.http import HttpResponseRedirect, JsonResponse, Http404

from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from main.models.users import User
from tickets.models import Ticket, TicketComment, transaction, TicketHistory, TicketCommentHistory
from tickets.forms import TicketForm, TicketCommentForm, TicketEditStatusForm, TicketSettingsForm
from main.mixins import LoginAndValidationRequiredMixin
from tickets.permissions import can_see_ticket, can_edit_ticket
from util.security.group_access import can_access_group, get_users_with_extended_rbac_to_group,  get_all_groups_for_user_with_extended_rbac, is_a_manager, is_manager_of_this_role


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
        # Using a session variable to keep track of whether this user can see all
        # validated users in the Ticket Owner dropdown list
        show_all_users = self.request.session.get(
            'owner_displays_all_validated_users')
        if show_all_users is None:
            show_all_users = False
        # here is where a change can take place....
        show_all_users = show_all_users and is_admin
        self.request.session['owner_displays_all_validated_users'] = show_all_users

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

    def dispatch(self, request, *args, **kwargs):
        selected_role = request.GET.get('selected_role')
        current_user = self.request.user
        if selected_role:
            # It's an Ajax request, handle it differently
            the_role_object = get_object_or_404(Group, id=selected_role)

            if current_user.is_staff:
                showAllOwnerOptions = self.request.session.get(
                    'owner_displays_all_validated_users')
                if showAllOwnerOptions:
                    potential_owners_for_the_role = User.objects.filter(
                        validated=True)
                else:
                    potential_owners_for_the_role = get_users_with_extended_rbac_to_group(
                        the_role_object)

            elif is_manager_of_this_role(current_user, the_role_object):
                potential_owners_for_the_role = get_users_with_extended_rbac_to_group(
                    the_role_object)

            else:
                if (can_access_group(current_user, the_role_object.id)):
                    # The user can assign themselves as Owner.
                    potential_owners_for_the_role = User.objects.filter(
                        id=current_user.id)
                else:
                    ################################################
                    # This case occurs when either
                    # A)The user is a manager, but this is a role
                    #    they neither manage nor are a member of.
                    #    (However, being a manager they can still move
                    #    the ticket to this or any other role)
                    # B) Or the user has selected a Role/Group that
                    #    they have no connection with. All users can
                    #    do this on creation, with the default_ticket_support
                    #    role.
                    # In either case, we will just show the default
                    #  (empty) owner list
                    ######################################################
                    potential_owners_for_the_role = get_users_with_extended_rbac_to_group()

            owner_options = []
            owner_options.append({'value': "",  'label': "---------"})

            for user_option in potential_owners_for_the_role:
                owner_options.append(
                    {'value': user_option.pk,  'label': str(user_option.name)})

            data = {'message': f'Newly Selected Role: {selected_role}',
                    'status': 'success',  'options': owner_options}
            return JsonResponse(data)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):

        # this is the group that that a new Ticket's Role field will be set
        # to by default.  This will be the only option available for
        # users with no roles and no special privileges to create their
        # tickets in. group_created is just to catch the unused T/F result.
        default_role, group_created = Group.objects.get_or_create(
            name='default_ticket_support')
        all_groups = Group.objects.all()
        current_user = self.request.user
        # Does this user manage ANY role/group?
        is_a_role_manager = is_a_manager(current_user)
        is_admin = current_user.is_staff

        # If I'm staff or a manager,  I can change the ticket to any role
        # and my preloaded owner options are any users who are in
        # the default role (if any,  otherwise we get an empty select list)
        if is_admin or is_a_role_manager:
            role_options = all_groups
            if is_admin:
                showAllOwnerOptions = self.request.session.get(
                    'owner_displays_all_validated_users')
                if showAllOwnerOptions:
                    owner_options = User.objects.filter(validated=True)
                else:
                    owner_options = get_users_with_extended_rbac_to_group(
                        default_role)
            elif is_manager_of_this_role(current_user, default_role):
                owner_options = get_users_with_extended_rbac_to_group(
                    default_role)
            else:
                owner_options = get_users_with_extended_rbac_to_group()

        else:
            # If I am not a staff or a manager,  I may not assign the
            # ticket to any *user* to be the Ticket Owner
            # (calling this with no role returns an empty list of users)
            owner_options = get_users_with_extended_rbac_to_group()
            # ..but I can assign the ticket to any *role* I have access to
            user_roles = get_all_groups_for_user_with_extended_rbac(
                current_user)
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

    # Dynamically repopulates the Owner dropdown list,
    # without reloading the whole form, when the user
    # changes the role selected in the Role dropdown.
    #
    # (Google Gemini suggested using the dispatch function
    # to check for AJAX call to give back a JSONResponse)
    #

    def dispatch(self, request, *args, **kwargs):
        selected_role = request.GET.get('selected_role')
        current_user = self.request.user
        if selected_role:
            # It's an Ajax request, handle it differently
            the_role_object = get_object_or_404(Group, id=selected_role)

            # permission flag: May the User see the option to set Owner to empty?
            can_set_ticket_owner_blank = False

            ticket = get_object_or_404(Ticket, id=self.kwargs.get('pk'))
            # Theorectically,  we'll never user ticket_owner when it's None but JIC...
            ticket_owner = None
            ticket_has_owner = ticket.owner is not None

            if ticket_has_owner:
                # sometimes I need the object itself,  other times the filtered queryset
                # other times,  I'd like to use the boolean I just created.
                ticket_owner = User.objects.filter(id=ticket.owner.id)
                ticket_owner_object = get_object_or_404(
                    User, id=ticket.owner.id)
            else:
                can_set_ticket_owner_blank = True

            if current_user.is_staff:
                can_set_ticket_owner_blank = True
                showAllOwnerOptions = self.request.session.get(
                    'owner_displays_all_validated_users')
                if showAllOwnerOptions:
                    potential_owners_for_the_role = User.objects.filter(
                        validated=True)
                else:
                    if ticket_has_owner and the_role_object == ticket.role:
                        potential_owners_for_the_role = get_users_with_extended_rbac_to_group(
                            the_role_object) | ticket_owner
                    else:
                        potential_owners_for_the_role = get_users_with_extended_rbac_to_group(
                            the_role_object)

            elif is_manager_of_this_role(current_user, the_role_object):
                if ticket_has_owner and the_role_object == ticket.role:
                    # If we are back on the ticket role, we need to
                    # account for the case where a Staff member has
                    # assigned someone outside the role to the ticket.
                    # We don't want to lose to option of that Ticket
                    # Owner until the ticket is saved.
                    potential_owners_for_the_role = get_users_with_extended_rbac_to_group(
                        the_role_object) | ticket_owner
                else:
                    potential_owners_for_the_role = get_users_with_extended_rbac_to_group(
                        the_role_object)

                can_set_ticket_owner_blank = True

            elif is_a_manager(current_user):

                if not (ticket_has_owner and the_role_object == ticket.role):
                    can_set_ticket_owner_blank = True
                    # else: The original setting of False will stick.
                    #
                    # if we have moved back to the saved ticket role, there is an
                    # owner selected for this role,  and we are NOT the manager
                    # of **this** role,  we cannot change it empty right now.
                    # While managers can move other managers tickets to other roles,
                    # we probably want to discourage them from simply meddling
                    # within another Manager's group by "unassigning" their tickets.

                if (can_access_group(current_user, the_role_object.id)):
                    # A manager user can assign themselves as Owner if they are
                    # part of the group,  even if this is not the group that
                    # they manage.
                    #
                    # If the Ticket has an owner, and that owner has access
                    # to the newly selected_role,  they can select the owner.
                    #
                    # The ticket owner will also become visible in this case:
                    # The Ticket's *saved*, assigned owner was mismatched with the
                    # Ticket's *saved *role, (by Staff).
                    # Now if this manager user selects another role,
                    # *without saving*,  and then navigates *back* to the currently
                    # **saved** Ticket role , they can still see the owner.
                    # (This way a manager can select another role for the ticket,  change
                    # their mind and go back to the original role,  without losing the
                    # "specially assigned" (mismatched) owner that Staff put on the Ticket.)

                    if ticket_has_owner and (the_role_object == ticket.role or can_access_group(ticket_owner_object, the_role_object.id)):
                        potential_owners_for_the_role = User.objects.filter(
                            id=current_user.id) | ticket_owner
                    else:
                        potential_owners_for_the_role = User.objects.filter(
                            id=current_user.id)
                else:
                    ################################################
                    # This case occurs when the user is a manager,
                    # but this is not one of the roles they manage,
                    # and they are not a member of this  role.
                    # (However, being a manager they can still move
                    #  the ticket to this or any other role)
                    # They cannot assign themselves as Ticket
                    # Owner. Usually,  they set the ticket owner
                    # # to blank when they change roles,  except when
                    # there is already a saved Ticket owner and:
                    # 1) The Ticket Owner is a member of the role just selcted.
                    # 2) The user has re-selected the Ticket's saved role -
                    #    even if the Ticket Owner is not part of the newly
                    #    seleted role
                    if ticket_has_owner and ((the_role_object == ticket.role) or can_access_group(ticket_owner_object, the_role_object.id)):
                       # TODO If the user is a manager,  can they set an
                       # *assigned owner* ticket to empty?
                        potential_owners_for_the_role = ticket_owner
                    else:  # just show the default (empty) owner list
                        potential_owners_for_the_role = get_users_with_extended_rbac_to_group()

            else:  # We SHOULDN'T hit this code.
                raise Http404(
                    "Non-privileged user tried to change roles on existing ticket. No code path should have permitted this. ")

            owner_options = []
            if can_set_ticket_owner_blank:
                owner_options.append({'value': "",  'label': "---------"})

            if not ticket_has_owner:
                for user_option in potential_owners_for_the_role:
                    owner_options.append(
                        {'value': user_option.pk,  'label': str(user_option.name)})
            else:
                for user_option in potential_owners_for_the_role:
                    is_selected = False
                    if user_option.pk == ticket_owner_object.pk:
                        is_selected = True

                    owner_options.append(
                        {'value': user_option.pk,  'label': str(user_option.name), 'selected': is_selected})

            data = {'message': f'Newly Selected Role: {selected_role}',
                    'status': 'success',  'options': owner_options}
            return JsonResponse(data)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('ticket', kwargs={'pk': self.object.id})

    # TODO: You'll notice that sections of dispatch and
    # get_context_data are flatly transgressing DRY.
    # If you try to make them more DRY,  just keep the
    # differences in mind:  get_context_data is getting
    # the context for a Ticket being loaded out of the database
    # for editing. It needs to determine the
    # available roles for this particular user.
    # The similar section in dispatch does NOT need to be
    # fed the list of roles again. It is responding to
    # on-the-fly changes the user makes to the role,
    # and only needs to re-do the Owner dropdown list.
    # Also, dispatch has to account for the case where
    # the user selects a different role, and then
    # reselects the original ticket role before
    # saving. In this case it needs to ensure the
    # user doesn't lose access to the specially
    # designated/mismatched owner that is not part
    # of the role.
    # )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ticket = get_object_or_404(Ticket, id=self.kwargs.get('pk'))

        current_user = self.request.user

        # May the User see the option to set Owner to empty?
        can_set_ticket_owner_blank = False

        # Both a value and a flag.
        # Determines if the "no owner" option is
        # available to the user
        ticket_owner = None
        ticket_has_owner = ticket.owner is not None

        if ticket_has_owner:
            ticket_owner = User.objects.filter(id=ticket.owner.id)
        else:
            can_set_ticket_owner_blank = True

        # For existing tickets,  the default role
        # is the currently saved Ticket Role
        currently_saved_role = ticket.role
        users_in_currently_saved_role = get_users_with_extended_rbac_to_group(
            currently_saved_role)
        all_groups = Group.objects.all()

        is_admin = current_user.is_staff
        if is_admin:
            can_set_ticket_owner_blank = True
            role_options = all_groups
            show_all_owner_options = self.request.session.get(
                'owner_displays_all_validated_users')
            if show_all_owner_options:
                owner_options = User.objects.filter(validated=True)
            else:
                # Get all users in the role; handle case where Staff has
                # already assigned the Ticket to a user outside the role.
                if ticket_has_owner:
                    owner_options = users_in_currently_saved_role | ticket_owner
                else:
                    owner_options = users_in_currently_saved_role

        elif is_manager_of_this_role(current_user, ticket.role):
            can_set_ticket_owner_blank = True
            role_options = all_groups
            if ticket_has_owner:
                # account for the case where a Staff member has
                # assigned someone outside the role to the ticket.
                # We don't want to lose to option of that Ticket
                # Owner until the ticket is saved.
                owner_options = get_users_with_extended_rbac_to_group(
                    ticket.role) | ticket_owner
            else:
                owner_options = get_users_with_extended_rbac_to_group(
                    ticket.role)
        else:
            # Does this user manage ANY role/group?
            if is_a_manager(current_user):
                # A manager can change the ticket to any role
                role_options = all_groups
            else:
                # If I am not a privileged user,
                # I must leave the ticket
                # in the role it is currently in.
                role_options = Group.objects.filter(
                    pk=currently_saved_role.pk)

            if (can_access_group(current_user, ticket.role.id)):
                # The user can assign themselves as Owner.
                # If the ticket has an owner, they can see that as well
                if ticket_has_owner:
                    owner_options = User.objects.filter(
                        id=current_user.id) | ticket_owner
                else:
                    owner_options = User.objects.filter(
                        id=current_user.id)

            else:

                # If I am not connected with any role, I may not assign to anyone else,
                # ... but I can see the current owner, if there is one

                if ticket_has_owner:
                    owner_options = ticket_owner
                else:  # just show the default (empty) owner list
                    owner_options = get_users_with_extended_rbac_to_group()

        # Note that can_set_owner_blank = True EITHER means: 1) The Ticket has no owner
        # or 2) The user is a Group Manager or Staff member,  who has permission
        # to make an assigned Ticket "Unassigned" again.  (or both)
        form = TicketForm(can_set_ticket_owner_blank=can_set_ticket_owner_blank, role_options=role_options, owner_options=owner_options,
                          role_default=currently_saved_role, owner_default=ticket_owner, instance=ticket)

        context['form'] = form
        context['is_admin'] = is_admin
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


class TicketSettings(LoginAndValidationRequiredMixin, UserPassesTestMixin, View):
    template_name = "ticket_owner_list_settings.html"

    def get(self, request):
        context = {}

        show_all_users = self.request.session.get(
            'owner_displays_all_validated_users')
        if show_all_users:
            initial_value = 1
        else:
            initial_value = 0
        form = TicketSettingsForm(
            initial={'show_all_users': initial_value})

        context["form"] = form
        context["primary_title"] = "Ticket Settings"
        return render(request, self.template_name, context)

    def post(self, request):
        form = TicketSettingsForm(request.POST)
        if form.is_valid():
            form_value = int(form.cleaned_data['show_all_users'])
            if form_value:  # 1, Truthy
                show_all_users = True
            else:  # 0, Falsy
                show_all_users = False

            self.request.session['owner_displays_all_validated_users'] = show_all_users

            return redirect('tickets')

        context = {}
        context["form"] = form
        context["primary_title"] = "Ticket Settings"
        return render(request, self.template_name, context)

    def test_func(self):
        if self.request.user.is_staff:
            return True


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
