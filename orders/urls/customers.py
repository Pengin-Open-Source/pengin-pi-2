from django.urls import path
from orders.views.customers import (ListCustomers,
                                    CreateCustomer,
                                    DetailCustomer,
                                    EditCustomer,
                                    DeleteCustomer,)
from orders.views.shipping_address import CreateShippingAddress, EditShippingAddress, DeleteShippingAddress

# Add namespace to urls
app_name = 'customers'

urlpatterns = [
    path('', ListCustomers.as_view(), name='list-customers'),
    path('<uuid:customer_id>/', DetailCustomer.as_view(), name='detail-customer'),
    path('create/', CreateCustomer.as_view(), name='create-customer'),
    path('<uuid:customer_id>/edit/', EditCustomer.as_view(), name='edit-customer'),
    path('<uuid:customer_id>/delete/', DeleteCustomer.as_view(), name='delete-customer'),
    path('<uuid:customer_id>/shipping-address/',
         CreateShippingAddress.as_view(),
         name='create-address'),
    path('<uuid:customer_id>/shipping-address/<uuid:address_id>/',
         EditShippingAddress.as_view(),
         name='edit-address'),
    path('<uuid:customer_id>/shipping-address/<uuid:address_id>/delete/',
         DeleteShippingAddress.as_view(),
         name='delete-address'),
]
