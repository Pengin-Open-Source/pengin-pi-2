from django.urls import path
from companies.views import (
    CompaniesHomeView, CompaniesListView, CompanyDetailView,  create_company, edit_company_info_post,
    display_company_members, edit_company_members, edit_company_members_post
)

urlpatterns = [
    # Main company display page
    path('company/', CompaniesHomeView.as_view(), name='display_companies_home'),
    path('company/list/', CompaniesListView.as_view(), name='companies_list'),
    path('company/create/', create_company, name='create_company'),
    path('company/<uuid:pk>/',
         CompanyDetailView.as_view(), name='display_company_info'),
    path('company/<uuid:company_id>/edit/',
         edit_company_info_post, name='edit_company_info_post'),
    path('company/<uuid:company_id>/members/',
         display_company_members, name='display_company_members'),
    path('company/<uuid:company_id>/members/edit/',
         edit_company_members, name='edit_company_members'),
    path('company/<uuid:company_id>/members/edit/save/',
         edit_company_members_post, name='edit_company_members_post'),
]
