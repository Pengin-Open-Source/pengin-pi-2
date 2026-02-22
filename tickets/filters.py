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

    summary = django_filters.ChoiceFilter(
        lookup_expr='icontains', label='Search Ticket Summaries....',
        choices=[],
        widget=forms.Select(
            attrs={'class': 'tom-select-enabled'})
    )

    content = django_filters.CharFilter(
        lookup_expr='icontains', label='Search Ticket Contents....')

    role = django_filters.ChoiceFilter(field_name='role__name',  # Actually searches the Group table's name field
                                       lookup_expr='icontains', label='Search Ticket by Role....',
                                       choices=[],
                                       widget=forms.Select(
                                           attrs={'class': 'tom-select-enabled'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        visible_tickets = self.queryset
        title_options = visible_tickets.values_list(
            'summary', flat=True).distinct()

        ticket_role_options = sorted(list(set(visible_tickets.values_list(
            'role__name', flat=True))))
        self.filters['summary'].extra['choices'] = [
            (t, t) for t in title_options]
        self.filters['role'].extra['choices'] = [
            (t, t) for t in ticket_role_options]

    class Meta:
        model = Ticket
        fields = ['priority', 'summary', 'role', 'content', 'tags']
