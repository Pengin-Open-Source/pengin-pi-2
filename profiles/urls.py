from django.urls import path
from .views import ProfileView, SendEmailView, ValidateView, EditProfileView, EditPasswordView, UserGroupListView

app_name = 'profiles'

urlpatterns = [
    path('', ProfileView.as_view(), name='profile'),
    path('group_lists/<group_filter>',
         UserGroupListView.as_view(), name='display_user_groups'),
    path('send_email/', SendEmailView.as_view(), name='send_email'),
    path('validate/<str:token>/', ValidateView.as_view(), name='validate'),
    path('edit_profile/', EditProfileView.as_view(), name='edit_profile'),
    path('edit_password/', EditPasswordView.as_view(), name='edit_password'),
]
