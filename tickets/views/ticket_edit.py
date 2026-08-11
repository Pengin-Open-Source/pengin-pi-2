# Ticket Status, Edit,  Delete
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import UpdateView, DeleteView
from main.mixins import LoginAndValidationRequiredMixin
from main.models import User
from tickets.forms import TicketForm, TicketEditStatusForm
from tickets.models import Ticket, TicketOpenRequest, transaction
from tickets.permissions import (
    can_edit_ticket,
    can_edit_ticket_privileged,
    is_ticket_manager,
    can_edit_ticket_status,
)
from tickets.views.util import delete_ticket
from util.security.group_access import (
    can_access_group,
    get_users_with_extended_rbac_to_group,
    is_a_manager,
    is_manager_of_this_role,
)


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

            # permission flag: May the User
            # see the option to set Owner to empty?
            can_set_ticket_owner_blank = False

            ticket = get_object_or_404(Ticket, id=self.kwargs.get('pk'))
            # Theorectically,  we'll never use ticket_owner when it's
            # None but JIC...
            ticket_owner = None
            ticket_has_owner = ticket.owner is not None

            if ticket_has_owner:
                # sometimes I need the object itself,  other times the filtered
                # queryset other times,  I'd like to use the boolean I just created.
                ticket_owner = User.objects.filter(
                    id=ticket.owner.id).distinct()
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
                            the_role_object).distinct() | ticket_owner
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
                        the_role_object).distinct() | ticket_owner
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
                    # While managers can move other managers' tickets to other roles,
                    # we probably want to discourage them from simply meddling
                    # within another Manager's group by "unassigning" their tickets.

                if (can_access_group(current_user, the_role_object.id)) and ticket.resolution_status != 'closed':
                    # A manager user can assign themselves as Owner if they are
                    # part of the group,  even if this is not the group that
                    # they manage. ETA - IF THE TICKET IS NOT CLOSED!!
                    #
                    # The ticket owner also becomes an option in this case:
                    # The Ticket's *saved*, assigned owner was mismatched with the
                    # Ticket's *saved *role, (by Staff).
                    # Now if this manager user selects another role,
                    # *without saving*,  and then navigates *back* to the currently
                    # **saved** Ticket role , they can still see the owner.
                    # (This way a manager can select another role for the ticket,  change
                    # their mind and go back to the original role,  without losing the
                    # "specially assigned" (mismatched) owner that Staff put on the Ticket.)

                    if ticket_has_owner and (the_role_object == ticket.role):
                        potential_owners_for_the_role = User.objects.filter(
                            id=current_user.id).distinct() | ticket_owner
                    else:
                        potential_owners_for_the_role = User.objects.filter(
                            id=current_user.id)
                else:
                    ################################################
                    # This case occurs when the user is a manager,
                    # but this is not one of the roles they manage,
                    # and they are not a member of this role,
                    # (ETA - OR THEY ARE A MEMBER, BUT THE TICKET IS CLOSED)
                    # (However, being a manager they can still move
                    #  the ticket to this or any other role)
                    # They cannot assign themselves as Ticket
                    # Owner. Usually,  they set the ticket owner
                    # to blank when they change roles,  except when
                    # there is already a saved Ticket owner and:
                    # the user has re-selected the Ticket's saved role -
                    # even if the Ticket Owner is not part of the newly
                    # seleted role
                    if ticket_has_owner and (the_role_object == ticket.role):
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
    # I don't account for that here in get_context_data
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
            ticket_owner = User.objects.filter(id=ticket.owner.id).distinct()
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
                    owner_options = users_in_currently_saved_role.distinct() | ticket_owner
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
                    ticket.role).distinct() | ticket_owner
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
            # if the user can access the group AND THE TICKET IS NOT CLOSED, they can assign themselves.
            if (can_access_group(current_user, ticket.role.id)) and ticket.resolution_status != 'closed':
                # The user can assign themselves as Owner.
                # If the ticket has an owner, they can see that as well
                if ticket_has_owner:
                    owner_options = User.objects.filter(
                        id=current_user.id).distinct() | ticket_owner
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
        role_options = role_options.order_by('name')
        form = TicketForm(can_set_ticket_owner_blank=can_set_ticket_owner_blank, role_options=role_options, owner_options=owner_options,
                          role_default=currently_saved_role, owner_default=ticket_owner, instance=ticket, current_user=current_user)

        # Users who can edit Priority, Summary, Content, and Tags:
        # Owner, Manager,  Staff, Author
        # (Check method for changes to this list)
        if not can_edit_ticket_privileged(current_user, ticket):
            # Have to actually disable the priority field in order to stop
            # the user from changing fields - it's a select field.
            form.fields['priority'].widget.attrs['disabled'] = 'disabled'
            form.fields['summary'].widget.attrs['readonly'] = 'readonly'
            form.fields['content'].widget.attrs['readonly'] = 'readonly'
            form.fields['tags'].widget.attrs['readonly'] = 'readonly'
        context['form'] = form
        context['is_admin'] = is_admin
        context['primary_title'] = "Ticket #" + \
            str(ticket.ticket_number) + ": " + ticket.summary
        context['ticket_id'] = self.object.id

        return context

    def post(self, request, *args, **kwargs):
        ticket_id = self.kwargs.get('pk')
        ticket = get_object_or_404(
            Ticket, id=ticket_id)

        # Gemini's advice on how to handle maintaining the Priority
        # value displayed upon save without errors
        # even if the Priority field is disabled.
        post_data = request.POST.copy()
        if 'priority' not in post_data:
            post_data['priority'] = ticket.priority

        current_user = self.request.user
        ticket_form = TicketForm(
            post_data, instance=ticket, current_user=current_user)
        if ticket_form.is_valid():
            # ticket = ticket_form.save(commit=False)
            ticket_to_be_edited = ticket_form.instance
            ticket_to_be_edited.last_edited_by = request.user
            ticket_to_be_edited.row_action = 'EDIT'

            # did the user actually change anything before
            # hitting Save?
            user_made_real_change = ticket_form.has_changed()

            # If *CURRENT* resolution_status is NOT Open,
            # and the user has made a REAL change, Reopen this ticket.
            handle_requests = False
            reopen_requests_pending = None
            if ticket.resolution_status != 'open' and user_made_real_change:
                ticket.last_edited_by = request.user
                ticket.row_action = 'EDIT'
                ticket.resolution_status = 'open'
                ticket.resolution_date = None
                # are there any outstanding re-open requests?
                # they need to be marked as handled
                reopen_requests_pending = ticket.reopen_requests.filter(
                    approval_status='pending')
                if reopen_requests_pending.exists():
                    handle_requests = True

            ticket_to_be_edited.date = timezone.now()
            ticket_form.instance = ticket_to_be_edited

            if handle_requests:
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
                    ticket = ticket_form.save()
            else:
                ticket = ticket_form.save()
            return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': ticket.id}))
        else:
            context = {}
            context['form'] = ticket_form
            context['is_admin'] = self.request.user.is_staff
            context['primary_title'] = "Ticket #" + \
                str(ticket.ticket_number) + ": " + ticket.summary
            context['ticket_id'] = ticket.id
            return render(request, self.template_name,  context)

    def test_func(self):

        ticket = self.get_object()
        return can_edit_ticket(self.request.user, ticket)


class TicketDeleteView(LoginAndValidationRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ticket

    def post(self, request, *args, **kwargs):
        ticket = self.get_object()
        delete_ticket(request.user, ticket)

        return HttpResponseRedirect(reverse_lazy('tickets'))

    def test_func(self):
        if self.request.user.is_staff:
            return True

        ticket = self.get_object()

        if is_ticket_manager(self.request.user, ticket):
            return True


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
