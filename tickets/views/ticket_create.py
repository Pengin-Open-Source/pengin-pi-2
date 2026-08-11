from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from main.mixins import LoginAndValidationRequiredMixin
from main.models import User
from tickets.forms import TicketForm
from tickets.models import Ticket
from util.security.group_access import (
    get_all_groups_for_user_with_extended_rbac,
    get_users_with_extended_rbac_to_group,
    is_a_manager,
    is_manager_of_this_role,
)


class TicketCreateView(LoginAndValidationRequiredMixin, CreateView):
    """Handles the creation of new tickets."""
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
                ################################################
                # The user is not staff or the manager
                # *** of this specific role**.
                # We will just show the default (empty) owner list
                # Users with any roles may come back and EDIT
                # the ticket and assign themselves as the owner
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
                current_user).distinct()
            default_role_as_queryset = Group.objects.filter(
                pk=default_role.pk).distinct()
            if user_roles.exists():
                # Get all the roles the user is connected with
                # + the default_ticket_support role
                role_options = user_roles | default_role_as_queryset
            else:
                # If I am not connected with any role,  I must assign the ticket
                # to default ticket support,  leaving management to assign it
                # to the correct role and owner later in the Edit Ticket page.
                role_options = Group.objects.filter(pk=default_role.pk)

        role_options = role_options.order_by('name')
        form = TicketForm(role_options=role_options,
                          owner_options=owner_options, role_default=default_role, current_user=current_user)
        context = {'form': form}
        return render(request, self.template_name,  context)

    def post(self, request):
        form = TicketForm(request.POST, current_user=request.user)
        if form.is_valid():
            form.instance.author = self.request.user
            form.instance.row_action = 'CREATE'
            form.instance.resolution_status = 'open'
            ticket = form.save()
            return HttpResponseRedirect(reverse_lazy('ticket', kwargs={'pk': ticket.pk}))
