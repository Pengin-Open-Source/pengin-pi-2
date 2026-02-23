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
            attrs={'class': 'tom-select-enabled'},
            choices=[])
    )

    content = django_filters.CharFilter(
        lookup_expr='icontains', label='Search Ticket Contents....')

    role = django_filters.CharFilter(field_name='role__name',  # Actually searches the Group table's name field
                                     lookup_expr='icontains', label='Search Ticket by Role....',
                                     widget=forms.Select(
                                         attrs={'class': 'tom-select-enabled'}, choices=[],))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        visible_tickets = self.queryset
        title_options = visible_tickets.values_list(
            'summary', flat=True).distinct()
        title_choices = [(t, t) for t in title_options]
        title_choices.insert(0, ('', "{Any Title}"))
        existing_title_values = {title[0] for title in title_choices}

        current_title = self.data.get('summary')
        if current_title and current_title not in existing_title_values:
            title_choices.insert(0, (current_title, current_title))

        ticket_role_options = sorted(list(set(visible_tickets.values_list(
            'role__name', flat=True))))

        role_choices = [(t, t) for t in ticket_role_options]
        role_choices.insert(0, ('', "{Any Group/Role}"))
        existing_role_values = {role[0] for role in role_choices}

        current_role = self.data.get('role')
        if current_role and current_role not in existing_role_values:
            role_choices.insert(0, (current_role, current_role))

        self.filters['summary'].extra['widget'].choices = title_choices

        self.filters['role'].extra['widget'].choices = role_choices

    class Meta:
        model = Ticket
        fields = ['priority', 'summary', 'role', 'content', 'tags']
