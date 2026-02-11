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

    role = django_filters.CharFilter(field_name='role__name',  # Actually searches the Group table's name field
                                     lookup_expr='icontains', label='Search Ticket by Role....',
                                     widget=forms.TextInput(attrs={'list': 'role-options', 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        visible_tickets = self.queryset
        title_options = visible_tickets.values_list(
            'summary', flat=True).distinct()
        self.filters['summary'].extra['choices'] = [
            (t, t) for t in title_options]
        # self.filters['category'].extra['queryset'] = self.queryset

    class Meta:
        model = Ticket
        fields = ['priority', 'summary', 'role', 'content', 'tags']
