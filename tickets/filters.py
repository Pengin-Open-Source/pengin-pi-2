import django_filters
from tickets.models import Ticket
from django import forms


class TicketFilter(django_filters.FilterSet):

    priority = django_filters.ChoiceFilter(
        choices=(
                ('LOW', 'Low'),
                ('MEDIUM', 'Medium'),
                ('HIGH', 'High'),
        ),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    summary = django_filters.CharFilter(
        lookup_expr='icontains', label='Search Ticket Summaries....',
        widget=forms.Select(
            attrs={'class': 'tom-select-enabled', 'multiple': 'multiple'},
            choices=[])
    )

    content = django_filters.CharFilter(
        lookup_expr='icontains', label='Search Ticket Contents....',
        widget=forms.Select(
            attrs={'class': 'tom-select-enabled', 'multiple': 'multiple'},
            choices=[])
    )

    role = django_filters.CharFilter(field_name='role__name',  # Actually searches the Group table's name field
                                     lookup_expr='icontains', label='Search Ticket by Role....',
                                     widget=forms.Select(
                                         attrs={'class': 'tom-select-enabled', 'multiple': 'multiple'}, choices=[],))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # PRE_LOADED FILTER DATA SECTION:
        # THESE FILTERS HAVE ACTUAL TICKET DATA
        # LOADED INTO THEM
        # The User's list of tickets,  with permissions and
        # status filtering applied.
        visible_tickets = self.queryset
        # Get all needed column values from queryset
        ticket_column_data = visible_tickets.values_list(
            'summary', 'role__name')

        title_options, role_options = set(), set()

        for row in ticket_column_data:
            title_options.add(row[0])
            role_options.add(row[1])

        # choices to display to user
        title_choices = [(t, t) for t in title_options]
        role_choices = [(t, t) for t in role_options]

        title_choices.insert(0, ('', "{Any Title}"))
        role_choices.insert(0, ('', "{Any Group/Role}"))

        # Any search criteria from the the user -
        # including those that don't match one of
        # the current options.
        current_title = self.data.get('summary')

        # current_role = self.data.get('role')
        current_roles = self.data.getlist('role')
        # print("What is the role?")
        # print(current_role)

        # check current options to see if
        # the search criteria is there.
        title_options.add("{Any Title}")
        role_options.add("{Any Group/Role}")

        if current_title and current_title not in title_options:
            title_choices.insert(0, (current_title, current_title))

        for role in current_roles:
            if role and role not in role_options:
                # Add the missing pill to the dropdown choices
                # so Django can mark it as "selected"
                role_choices.insert(0, (role, role))
                # Add to options too so we don't duplicate if the same
                # pill is somehow in the list twice
                role_options.add(role)

        # Add final set of choices to the search filter widgets
        self.filters['summary'].extra['widget'].choices = title_choices
        self.filters['role'].extra['widget'].choices = role_choices

        # NO TICKET DATA SECTION.
        # Fields that are NOT pre-loaded from the actual ticket data
        # for security, speed, or practical reasons.

        # But content will still use TomSelect and allow
        # user to have a list of previously used search terms.

        content_options = set()
        content_choices = []
        content_choices.insert(0, ('', "{Any Content}"))
        content_options.add("{Any Content}")
        current_content = self.data.get('content')

        if current_content and current_content not in content_options:
            content_choices.insert(0, (current_content, current_content))
        self.filters['content'].extra['widget'].choices = content_choices

        # Fields that don't use TomSelect, ie,  Dates.
        # #TODO Add date search ranges....

    class Meta:
        model = Ticket
        fields = ['priority', 'summary', 'role', 'content', 'tags']
