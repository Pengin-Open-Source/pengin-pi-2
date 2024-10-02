from django.urls import path
from companies.views import (
    CompaniesHomeView, CompaniesListView, CompanyDetailView,  CompanyCreateView, CompanyEditView,
    CompanyMembersListDetailView, CompanyMemberListUpdateView
)

urlpatterns = [
    # Main company display page
    path('company/', CompaniesHomeView.as_view(), name='display_companies_home'),
    path('company/list/', CompaniesListView.as_view(), name='companies_list'),
    path('company/create/',  CompanyCreateView.as_view(), name='create_company'),
    path('company/<uuid:pk>/',
         CompanyDetailView.as_view(), name='display_company_info'),
    path('company/<uuid:pk>/edit/',
         CompanyEditView.as_view(), name='edit_company_info_post'),
    path('company/<uuid:pk>/members/',
         CompanyMembersListDetailView.as_view(), name='display_company_members'),
    path('company/<uuid:pk>/members/edit/',
         CompanyMemberListUpdateView.as_view(), name='edit_company_members'),
    #     path('company/<uuid:company_id>/members/edit/save/',
    #          edit_company_members_post, name='edit_company_members_post'),
]
