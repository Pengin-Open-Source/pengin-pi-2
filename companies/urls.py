from django.urls import path
from .views import create_company, display_company_info, edit_company_info_post, display_company_members, edit_company_members, edit_company_members_post, display_companies_home

urlpatterns = [
    path('company/', display_companies_home, name='display_companies_home'),  # Main company display page
    path('company/create/', create_company, name='create_company'),
    path('company/<uuid:company_id>/', display_company_info, name='display_company_info'),
    path('company/<uuid:company_id>/edit/', edit_company_info_post, name='edit_company_info_post'),
    path('company/<uuid:company_id>/members/', display_company_members, name='display_company_members'),
    path('company/<uuid:company_id>/members/edit/', edit_company_members, name='edit_company_members'),
    path('company/<uuid:company_id>/members/edit/save/', edit_company_members_post, name='edit_company_members_post'),
]
#urls for companies


#urlpatterns

'''
/companies
/company
/company_create
/company_edit
/company_members
/company_members_edit

'''
