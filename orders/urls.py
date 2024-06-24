from django.urls import path
from .views.orders import ListOrders, CreateOrder, DetailOrder, EditOrder, DeleteOrder

# Add namespace to urls
app_name = 'orders'

urlpatterns = [
    path('', ListOrders.as_view(), name='list-orders'),
    path('<uuid:order_id>/', DetailOrder.as_view(), name='detail-order'),
    path('create/', CreateOrder.as_view(), name='create-order'),
    path('<uuid:order_id>/edit/', EditOrder.as_view(), name='edit-order'),
    path('<uuid:order_id>/delete/', DeleteOrder.as_view(), name='delete-order'),
]
