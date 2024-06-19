from django.urls import path
from .views import create_company, display_company_info, edit_company_info_post, display_company_members, edit_company_members, edit_company_members_post

urlpatterns = [
    path('company/create/', create_company, name='create_company'),
    path('company/<str:company_id>/', display_company_info, name='display_company_info'),
    path('company/<str:company_id>/edit/', edit_company_info_post, name='edit_company_info_post'),
    path('company/<str:company_id>/members/', display_company_members, name='display_company_members'),
    path('company/<str:company_id>/members/edit/', edit_company_members, name='edit_company_members'),
    path('company/<str:company_id>/members/edit/save/', edit_company_members_post, name='edit_company_members_post'),
]