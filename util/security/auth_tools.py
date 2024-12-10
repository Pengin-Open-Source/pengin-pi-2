from functools import wraps
from django.http import HttpResponseForbidden


def group_required(group_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # There is no group staff cannot access
            if request.user.is_authenticated and request.user.validated and (request.user.is_staff or request.user.groups.filter(name=group_name).exists()):
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden("<h1> You don't have permission to access this page. </h1>")
        return wrapped_view
    return decorator


def is_admin_provider(view_func):
    """
    Decorator for views that checks if the user is authenticated and is_staff.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        is_admin = request.user.is_authenticated and request.user.validated and request.user.is_staff
        return view_func(request, is_admin=is_admin, *args, **kwargs)
    return _wrapped_view


def is_admin_required(view_func):
    """
    Decorator for views that checks if the user is authenticated and is_staff.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.validated and request.user.is_staff:
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("<h1> You must be an admin to access this page. </h1>")
    return _wrapped_view


def user_group_provider(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        groups = []
        if request.user.is_authenticated and request.user.validated:
            groups = list(request.user.groups.values_list('name', flat=True))
        return view_func(request, groups=groups, *args, **kwargs)
    return wrapped_view
