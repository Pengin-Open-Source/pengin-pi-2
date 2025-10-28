from django import forms
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import get_object_or_404
from main.models.users import User
from tickets.models import Ticket, TicketComment, TicketOpenRequest
from django.db.models import QuerySet
from django.contrib.auth.models import Group
from util.forms.fields import UserModelChoiceField
from util.security.group_access import can_access_group, get_all_groups_for_user_with_extended_rbac, get_users_with_extended_rbac_to_group, is_a_manager, is_manager_of_this_role


class TicketForm(forms.ModelForm):

    owner = UserModelChoiceField(
        queryset=User.objects.filter(validated=True),
        required=False,
        error_messages={
            'not_valid': "Invalid Owner Selection",
        }
    )

    class Meta:
        model = Ticket
        fields = ['summary', 'role', 'owner', 'content', 'tags']

    def __init__(self, *args, can_set_ticket_owner_blank=True, role_options=None, owner_options=None, role_default=None, owner_default=None, **kwargs):
        self.current_user = kwargs.pop('current_user', None)

        super().__init__(*args, **kwargs)

        # I don't allow blank roles, so get rid of empty_label option:
        self.fields['role'].empty_label = None
        # assign the role options (mandatory) and owner options (optional)
        # to the dropdown picklists in the form.
        if role_options:
            self.fields['role'].queryset = role_options
        # Gemini's suggestion for avoiding treating an empty queryset as "None"
        if isinstance(owner_options, QuerySet):
            self.fields['owner'].queryset = owner_options
        # Creating a ticket should have default role of "default_ticket_support"
        # Editing should have default role of whatever was saved as the current role
        if role_default:
            self.fields['role'].initial = role_default
        # check flag to determine if the user
        # has permission to assign owner to *no one*
        # if not, get rid of  the "--------"  option.
        # and set the initial value to the owner_default
        if not can_set_ticket_owner_blank:
            # ASSUMPTION: in this case owner_default
            # *should* never have a value of None.
            # if does,  I want to see some kind of err
            # message
            self.fields['owner'].empty_label = None
            self.fields['owner'].initial = owner_default

    def clean(self):
        cleaned_data = super().clean()
        current_user = self.current_user

        # May the User see the option to set Owner to empty?
        can_set_ticket_owner_blank = False

        selected_role = cleaned_data.get('role')
        selected_owner = cleaned_data.get('owner')

        # make sure that the user didn't tamper with the role/owner options
        # on the client side: check roles and owner options again
        if self.instance and not self.instance._state.adding:
            ticket = self.instance

            # Users who can edit Summary, Content, and Tags:
            # Owner, Manager,  Staff, Author
            can_edit_text_fields = False
            if ticket.author == current_user:
                can_edit_text_fields = True

            # Determines if the "no owner" option is
            # available to the user
            saved_ticket_owner = None
            ticket_has_owner = ticket.owner is not None

            if ticket_has_owner:
                # the owner that is saved
                saved_ticket_owner = User.objects.filter(id=ticket.owner.id)
                if current_user.id == ticket.owner.id:
                    can_edit_text_fields = True
            else:
                can_set_ticket_owner_blank = True

            currently_saved_role = ticket.role

            all_groups = Group.objects.all()

            is_admin = current_user.is_staff
            if is_admin:
                can_edit_text_fields = True
                can_set_ticket_owner_blank = True
                role_options = all_groups
                owner_options = User.objects.filter(validated=True)
            elif is_manager_of_this_role(current_user, selected_role):
                can_set_ticket_owner_blank = True
                can_edit_text_fields = True
                role_options = all_groups
                if ticket_has_owner and selected_role == currently_saved_role:
                    # account for the case where a Staff member has
                    # assigned someone outside the role to the ticket,
                    # and the manager has selected the saved ticket role.
                    # We don't want to lose to option of that Ticket
                    # Owner until/unless the ticket is saved with a different
                    # owner or a different mismatched role.
                    owner_options = get_users_with_extended_rbac_to_group(
                        selected_role) | saved_ticket_owner
                else:
                    owner_options = get_users_with_extended_rbac_to_group(
                        selected_role)
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

                if (can_access_group(current_user, selected_role.id)):
                    # The user can assign themselves as Owner.
                    # If the ticket has an owner, and the they
                    # are on the saved role, they can see that as well
                    # (They should not have have been allowed to change
                    # roles if they were not a manager of any roles, but
                    # this method should catch them if they try to "cheat"
                    # and change roles with Browser Tools)
                    if ticket_has_owner and selected_role == currently_saved_role:
                        owner_options = User.objects.filter(
                            id=current_user.id) | saved_ticket_owner
                    else:
                        owner_options = User.objects.filter(
                            id=current_user.id)

                else:

                    # If I am not connected with any role, I may not assign to anyone else,
                    # ... but I can see the current owner, if there is one and I
                    # did not "cheat" and try to change from the saved role.

                    if ticket_has_owner and selected_role == currently_saved_role:
                        owner_options = saved_ticket_owner
                    else:  # just show the default (empty) owner list
                        owner_options = get_users_with_extended_rbac_to_group()

            if not selected_role in role_options:
                raise SuspiciousOperation(
                    "Warning! You are not allowed to select this Role!")

            owner_errors = self.errors.get('owner', [])
            if not selected_owner in owner_options:

                if selected_owner:
                    raise SuspiciousOperation(
                        "Warning! You are not allowed to select this Owner")
                elif owner_errors:
                    raise SuspiciousOperation(owner_errors)
                elif not can_set_ticket_owner_blank:
                    raise SuspiciousOperation(
                        "Warning! Empty Owner not allowed on this ticket!")

            # Stop certain users from editing
            # the content, even if they can see it.
            if not can_edit_text_fields:
                if ticket.content != cleaned_data.get('content'):
                    raise SuspiciousOperation(
                        "Warning! You are not allowed Edit the Content!")
                if ticket.tags != cleaned_data.get('tags'):
                    raise SuspiciousOperation(
                        "Warning! You are not allowed Edit the Tags!")
                if ticket.summary != cleaned_data.get('summary'):
                    raise SuspiciousOperation(
                        "Warning! You are not allowed Edit the Summary!")
        else:  # new Ticket
            can_set_ticket_owner_blank = True
            default_role = get_object_or_404(
                Group, name='default_ticket_support')

            all_groups = Group.objects.all()

            # Does this user manage ANY role/group?
            is_a_role_manager = is_a_manager(current_user)
            is_admin = current_user.is_staff

            # If I'm staff or a manager,  I can change the ticket to any role.
            # The valid owner options for:
            # 1) A Staff member - any validated users
            # 2) A manager of this role - any users belonging to the
            #    their role (if there are any,  otherwise we get
            #    an empty select list)
            # 3) Any other manager - empty list.
            if is_admin or is_a_role_manager:
                role_options = all_groups
                if is_admin:
                    owner_options = User.objects.filter(validated=True)
                elif is_manager_of_this_role(current_user, selected_role):
                    owner_options = get_users_with_extended_rbac_to_group(
                        selected_role)
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

            # stop this submit if the role or owner is not in the approved list

            if not selected_role in role_options:
                raise SuspiciousOperation(
                    "Warning! You are not allowed to select this Role!")

            owner_errors = self.errors.get('owner', [])
            if not selected_owner in owner_options:
                if selected_owner:
                    raise SuspiciousOperation(
                        "Warning! You are not allowed to select this Owner")
            elif owner_errors:
                raise SuspiciousOperation(owner_errors)
            elif not can_set_ticket_owner_blank:
                raise SuspiciousOperation(
                    "Warning! Empty Owner not allowed on this ticket!")

        return cleaned_data


class TicketEditStatusForm(forms.ModelForm):
   # I decided to put the selection choices in the form itself.
   # Gemini's suggestion on how:
    resolution_status = forms.ChoiceField(
        choices=(
                ('open', 'Open'),
                ('closed', 'Closed'),
                ('resolved', 'Resolved'),
        ),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Ticket
        fields = ['resolution_status']

    def __init__(self, *args, restrict_choices=False, **kwargs):
        # Always call the parent's init first
        super().__init__(*args, **kwargs)

        if restrict_choices:
            new_choices = (
                ('resolved', 'Resolved'),
                ('closed', 'Closed'),
            )
            self.fields['resolution_status'].choices = new_choices


class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ['content']

# Create a request to reopen a ticket


class TicketCreateOpenRequestForm(forms.ModelForm):

    class Meta:
        model = TicketOpenRequest
        fields = ['reason']


class TicketPendingOpenRequestForm(forms.ModelForm):
    author = UserModelChoiceField(
        queryset=User.objects.filter(validated=True),
        required=False,
        error_messages={
            'not_valid': "Invalid Owner Selection",
        }
    )

    class Meta:
        model = TicketOpenRequest
        fields = ['author', 'approval_status', 'reason']

    def __init__(self, *args, **kwargs):
        # Always call the parent's init first
        super().__init__(*args, **kwargs)

        self.fields['author'].initial = User.objects.filter(
            id=self.instance.author.id)


class TicketOpenRequestResponseForm(forms.ModelForm):
    class Meta:
        model = TicketOpenRequest
        fields = ['handler_comment']


class TicketSettingsForm(forms.Form):
    show_all_users = forms.ChoiceField(
        label='Users Shown in Owner Dropdown list',
        choices=[(0, "Users Associated with Selected Role"),
                 (1, "All Validated Users"),]
    )
