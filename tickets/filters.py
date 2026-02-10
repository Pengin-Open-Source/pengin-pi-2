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
        choices=[],
        widget=forms.TextInput(
            attrs={'class': 'tom-select-enabled'})
    )

    content = django_filters.CharFilter(
        lookup_expr='icontains', label='Search Ticket Contents....')

    role = django_filters.CharFilter(field_name='role__name',  # Actually searches the Group table's name field
                                     lookup_expr='icontains', label='Search Ticket by Role....',
                                     widget=forms.TextInput(attrs={'list': 'role-options', 'class': 'form-control'}))

    class Meta:
        model = Ticket
        fields = ['priority', 'summary', 'role', 'content', 'tags']
