import django_filters
from django_flatpickr.widgets import DateTimePickerInput
from tickets.models import Ticket
from django import forms
from django.db.models import Q


class TicketFilter(django_filters.FilterSet):

    priority = django_filters.ChoiceFilter(
        choices=(
                ('LOW', 'Low'),
                ('MEDIUM', 'Medium'),
                ('HIGH', 'High'),
        ),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    ticket_number = django_filters.CharFilter(
        method='filter_multiple_numbers', label='Search for Specific Ticket#....',
        widget=forms.SelectMultiple(
            attrs={'class': 'tom-select-enabled', 'multiple': 'multiple',
                   'data-default-empty-selection': '{Any Ticket #}'},
            choices=[])
    )

    summary = django_filters.CharFilter(
        method='filter_multiple_search_phrases', label='Search Ticket Summaries....',
        widget=forms.SelectMultiple(
            attrs={'class': 'tom-select-enabled', 'multiple': 'multiple',
                   'data-default-empty-selection': '{Any Title/Summary}'},
            choices=[])
    )

    content = django_filters.CharFilter(
        method='filter_multiple_search_phrases', label='Search Ticket Contents....',
        widget=forms.SelectMultiple(
            attrs={'class': 'tom-select-enabled', 'multiple': 'multiple',
                   'data-default-empty-selection': '{Any Content}'},
            choices=[])
    )
    role = django_filters.CharFilter(field_name='role__name',  # Actually searches the Group table's name field
                                     method='filter_foreign_key_name_attribute', label='Search Tickets by Role....',
                                     widget=forms.SelectMultiple(
                                         attrs={
                                             'class': 'tom-select-enabled', 'multiple': 'multiple',
                                             'data-default-empty-selection': '{Any Group/Role}'},
                                         choices=[],

                                     ))

    author = django_filters.CharFilter(field_name='author__name',  # Actually searches the User table's name field
                                       method='filter_foreign_key_name_attribute', label='Search Tickets by Author....',
                                       widget=forms.SelectMultiple(
                                           attrs={
                                               'class': 'tom-select-enabled', 'multiple': 'multiple',
                                               'data-default-empty-selection': '{Any Author}'},
                                           choices=[],

                                       ))

    owner = django_filters.CharFilter(field_name='owner__name',  # Actually searches the User table's name field
                                      method='filter_foreign_key_name_attribute', label='Search Tickets by Owner....',
                                      widget=forms.SelectMultiple(
                                          attrs={
                                              'class': 'tom-select-enabled', 'multiple': 'multiple',
                                              'data-default-empty-selection': '{Any Owner}'},
                                          choices=[],

                                      ))

    last_edited_by = django_filters.CharFilter(field_name='last_edited_by__name',  # Actually searches the User table's name field
                                               method='filter_foreign_key_name_attribute', label='Search by Last User to Edit....',
                                               widget=forms.SelectMultiple(
                                                   attrs={
                                                       'class': 'tom-select-enabled', 'multiple': 'multiple',
                                                       'data-default-empty-selection': '{Anyone}'},
                                                   choices=[],

                                               ))

    tags = django_filters.CharFilter(field_name='tags',  # Actually searches the Group table's name field
                                     method='filter_multiple_search_phrases', label='Search Ticket by Tags....',
                                     widget=forms.SelectMultiple(
                                         attrs={'class': 'tom-select-enabled', 'multiple': 'multiple',
                                                'data-default-empty-selection': '{Any Tags}'}, choices=[],))

    date = django_filters.DateTimeFilter( label='Created/Edited On Or After....', widget=DateTimePickerInput())

    # Gemini's suggestion for multiple terms selected for one search box,
    # refactored,  and re-used to deal with the foreign key /getlist problem

    # This version is generic. I use it for any field that's NOT
    # a foreign key and searches by text.

    def filter_multiple_search_phrases(self, queryset, name, _value):
        # 1. Django-filter might pass the values as a list or a comma-string
        # Let's ensure we have a list of terms
        values = self.data.getlist(name)

        if not values:
            return queryset

        return self.filter_mulitple_values(queryset, name,  values)

    # Called by filter methods searching for specific text or names
    def filter_mulitple_values(self, queryset, name, values):
        # Build a "Q object" for the OR search
        # This creates: Q({field_name}__icontains=val1) | Q({field_name}__icontains=val2) ...
        search_query = Q()
        for val in values:
            if val.strip() and val != '{None}':
                search_query |= Q(**{f"{name}__icontains": val})
            elif val == '{None}':
                search_query |= Q(**{f"{name}__isnull": True})

        return queryset.filter(search_query).distinct()

    # the foreign keys will be using their own methods,
    # to get the values and set the name, because
    # the 'name' field being used is NOT in getlist

    def filter_foreign_key_name_attribute(self, queryset, name, _value):
        # if we are filtering on the name attribute in
        # the model of a foreign key field, call this.
        # The reason is that the name parameter
        # will be given the argument "{field_name}__name",
        # while to extract the values from data, you will
        # need the command self.data.getlist('{field_name}')

        # strip off __name from field name
        field_name = name[:-6]
        values = self.data.getlist(field_name)

        if not values:
            return queryset

        return self.filter_mulitple_values(queryset, name, values)

    def filter_multiple_numbers(self, queryset, name, _value):
        # 1. Django-filter might pass the values as a list or a comma-string
        # Let's ensure we have a list of terms
        values = self.data.getlist(name)

        if not values:
            return queryset

        search_query = Q()
        for val in values:
            if val.strip() and val.isdigit():
                search_query |= Q(**{f"{name}__icontains": val})

        return queryset.filter(search_query).distinct()

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
            'ticket_number', 'summary', 'role__name', 'author__name', 'owner__name', 'last_edited_by__name', 'tags')

        ticket_number_options, title_options, role_options, author_options, owner_options, last_editor_options = set(
        ), set(), set(), set(), set(), set()

        for row in ticket_column_data:
            # check these options later
            # to see if an option needs
            # to be added.
            if str(row[0]).isdigit():
                ticket_number_options.add(row[0])
            title_options.add(row[1])
            role_options.add(row[2])
            author_options.add(row[3])
            ticket_owner = row[4]
            if ticket_owner is not None:
                owner_options.add(row[4])
            else:
                owner_options.add('{None}')

            ticket_editor = row[5]
            if ticket_editor is not None:
                last_editor_options.add(row[5])
            else:
                last_editor_options.add('{None}')

        tag_options = set([
            tag for row in ticket_column_data for tag in row[6].split()])

        self.update_search_options("ticket_number", ticket_number_options)
        self.update_search_options("summary", title_options)
        self.update_search_options("role", role_options)
        self.update_search_options("author", author_options)
        self.update_search_options("owner", owner_options)
        self.update_search_options("last_edited_by", last_editor_options)
        self.update_search_options("tags", tag_options)

        # NO TICKET DATA SECTION.
        # Fields that are NOT pre-loaded from the actual ticket data
        # for security, speed, or practical reasons.

        # But content will still use TomSelect and allow
        # user to have a list of previously used search terms.

        self.update_search_options("content", set())

        # Fields that don't use TomSelect, ie,  Dates.
        # #TODO Add date search ranges....

    def clean(self):
        cleaned_data = super().clean()
        ticket_numbers = cleaned_data.get('ticket_number')

        for number in ticket_numbers:
            if not number.isdigit():
                raise forms.ValidationError(
                    f"'{number}' is not a valid Ticket Number. Please use digits only."
                )

        return cleaned_data

    # refactor/tweak current code and Gemini suggestions - to get one method
    # to help account for multiple selections chosen in any field,  including
    # input from the user that doesn't match existing choices. (Adding it to the
    # dropdown in that case)

    def update_search_options(self, field_name, valid_options):
        # Any search criteria from the the user -
        # including those that don't match one of
        # the current options.
        current_selections_in_field = self.data.getlist(field_name)
        search_field = self.filters[field_name]
        empty_choice = search_field.extra.get(
            'widget').attrs.get('data-default-empty-selection')
        additional_choice = "{Add Another....}"

        if current_selections_in_field:
            default_choice = [('', additional_choice)]
        else:
            default_choice = [('', empty_choice)]

        # TODO use more generic code (not "hard-coded") for this
        # condition check if we start using multiple numeric fields
        if (field_name != "ticket_number"):
            for choice_pill in current_selections_in_field:
                if choice_pill and choice_pill not in [valid_options, empty_choice, additional_choice]:
                    # Add the choice to the options list.
                    valid_options.add(choice_pill)

            dropdown_choice_list = default_choice + \
                [(choice, choice)
                 for choice in sorted(valid_options, key=str.lower)]
        else:  # handle numeric field
            for choice_pill in current_selections_in_field:
                if choice_pill and str(choice_pill).isdigit() and choice_pill not in [valid_options, empty_choice, additional_choice]:
                    # Add the choice to the options list.
                    valid_options.add(choice_pill)

            sorted_options = sorted(valid_options, key=int)
            dropdown_choice_list = default_choice + \
                [(choice, choice)
                 for choice in sorted_options]

        self.filters[field_name].extra['widget'].choices = dropdown_choice_list

    class Meta:
        model = Ticket
        fields = ['priority', 'ticket_number',
                  'summary', 'role', 'content', 'author', 'owner', 'last_edited_by', 'tags', 'date']
