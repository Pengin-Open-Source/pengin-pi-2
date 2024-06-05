from django.core.paginator import Paginator, EmptyPage
from django.db.models import Count
from math import ceil

def paginate(queryset, page, per_page=10, filters=None):
    """
    Paginate Method for Django QuerySets
    This paginate method takes a Django QuerySet, a page number,
    and optional parameters: per_page, filters.
    
    Required Inputs:
        queryset: Django QuerySet
        page: int, the page number to be retrieved
    
    Optional Parameters:
        per_page: int, number of items per page, default is 10
        filters: dict, dictionary of filtering conditions, default is None
    
    Outputs:
        Paginated Django QuerySet
    """
    if filters is None:
        filters = {}
        
    paginator = Paginator(queryset, per_page)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj


def paginate_join(Model1, Model2, join_on, page, per_page=10, filters=None):
    """
    Paginate Method for JOINs in Django
    This paginate method takes two Django models, a join condition,
    a page number, and optional parameters: per_page, filters.
    
    Required Inputs:
        Model1: Django Model
        Model2: Django Model
        join_on: str, the join condition 
        page: int, the page number to be retrieved
    
    Optional Parameters:
        per_page: int, number of items per page, default is 10
        filters: dict, dictionary of filtering conditions, default is None
    
    Outputs:
        Paginated Django QuerySet
    """
    if filters is None:
        filters = {}
        
    try:
        queryset = Model1.objects.select_related(Model2).filter(**filters)
        paginator = Paginator(queryset, per_page)
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        return page_obj
    except Exception as e:
        count = Model1.objects.count()
        end = ceil(count / per_page)
        page_obj = paginator.page(end)
        return page_obj
