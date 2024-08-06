from django.urls import path
from .views import ListContracts, DetailContract, CreateContract, EditContract, DeleteContract


# Add namespace to urls
app_name = 'contracts'

urlpatterns = [
    path('', ListContracts.as_view(), name='list-contracts'),
    path('<uuid:contract_id>/', DetailContract.as_view(), name='detail-contract'),
    path('create/', CreateContract.as_view(), name='create-contract'),
    path('<uuid:contract_id>/edit/', EditContract.as_view(), name='edit-contract'),
    path('<uuid:contract_id>/delete/', DeleteContract.as_view(), name='delete-contract'),
]
