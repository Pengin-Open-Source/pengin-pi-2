from django.urls import path
from .views import product_list, product_detail, CreateProduct, EditProduct, delete_product

# Add namespace to urls
app_name = 'products'

urlpatterns = [
    path('', product_list, name='list-products'),
    path('<uuid:product_id>/', product_detail, name='detail-product'),
    path('create/', CreateProduct.as_view(), name='create-product'),
    path('<uuid:product_id>/edit/', EditProduct.as_view(), name='edit-product'),
    path('<uuid:product_id>/delete/', delete_product, name='delete-product'),
]



