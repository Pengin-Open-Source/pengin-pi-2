from django.shortcuts import get_object_or_404

from .models import Event
from django.db.models import OuterRef
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from main.models.users import SubGroup, GroupSpecialAccess
from util.security.group_access import get_cross_group_access, get_subgroups
SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']


# Allows duplication of an event, creation of a new event,
# and seeing all details of an event.
# A public event will hide the participant list from
# unauthorized users.
def can_create_or_see_all_event_details(current_user, event_id=None):
    if not current_user.is_authenticated:
        return False

    if event_id is None:
        return True
    # If the event exists, user has permission to see and duplicate it
    # if they are the event author, organizer, participant, or have a role associated with the event.
    # - or if they are staff.
    event = get_object_or_404(Event, id=event_id)
    user_groups = current_user.groups.all()

    # Retreive all the ancestor groups that the user's group is
    # a descendant of, using Subgroup closure table.
    user_super_groups = get_subgroups(user_groups)

    # Retrieve all the groups that the user's groups has special access to,
    # using the GroupSpecialAccess table
    # IMPORTANT. This has a KEY difference from being an actual member of a group/role
    # If the user merely has special access to a role,  they do NOT also
    # inherit the permissions from this group's ancestor roles
    user_accessed_groups = get_cross_group_access(user_groups)

    # A matching role is a group/role assigned to this event where:
    # The user has this role
    # The user has a role that is a descendant role of this role.
    # The user has a role that can access this role
    matching_role = event.roles.filter(
        id__in=user_groups).exists() or event.roles.filter(
        id__in=user_super_groups.filter(ancestor=OuterRef('id'))).exists() or event.roles.filter(id__in=user_accessed_groups.filter(
            accessed_group=OuterRef('id'))).exists()

    participant_ids = event.participants.values_list(
        'participant_id', flat=True)

    return (current_user.is_staff or matching_role or current_user.id in participant_ids or current_user in [event.author,  event.organizer])

# Anyone who does can NOT see all the details of an
# event,  can still see an event if it is:
# a) public
# b) within a year of today


def can_see_public_event(event):
    # Anyone can see public events that start or end
    # up to a year before or after now
    # credit to Gemini for help
    # with these calculations
    if event.is_public:
        right_now = timezone.now()
        start_datetime = event.start_datetime
        end_datetime = event.end_datetime

        if not time_difference_over_a_year(right_now, start_datetime):
            return True
        if not time_difference_over_a_year(right_now, end_datetime):
            return True
        if right_now > start_datetime and right_now < end_datetime:
            return True

    return False


def is_month_too_far_away(selected_year,  selected_month):

    # Gemini code snipet for getting the month, year
    # of the date a year ago & a year from now.
    # 1. Get the current, timezone-aware UTC datetime
    ################################################
    right_now = timezone.now()

    # 2. Calculate one year from now using relativedelta
    one_year_from_now = right_now + relativedelta(years=1)

    # 3. Calculate one year ago using relativedelta
    one_year_ago = right_now - relativedelta(years=1)

    # --- ONE YEAR FROM NOW ---
    future_month = one_year_from_now.month  # e.g., 11 (for November)
    future_year = one_year_from_now.year    # e.g., 2026

    # --- ONE YEAR AGO ---
    past_month = one_year_ago.month        # e.g., 11 (for November)
    past_year = one_year_ago.year          # e.g., 2024

    #############################################

    # is the calendar month selected too far away
    # to allow unauthorized users to see it?
    if selected_year > future_year or selected_year < past_year:
        return True
    elif selected_year == future_year and selected_month > future_month:
        return True
    elif selected_year == past_year and selected_month < past_month:
        return True
    
    return False


def can_change_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    # Only the author or organizer, or staff can change an event
    return request.user.is_staff or request.user in [event.author, event.organizer]


########## UTILITY METHODS ##################
# credit to Gemini for help with these calculations
def time_difference_over_a_year(date1, date2):
    earlier = min(date1, date2)
    later = max(date1, date2)

    return later > earlier + relativedelta(years=1)
