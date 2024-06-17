from django.urls import path
from .views import ListProduct, DetailProduct, CreateProduct, EditProduct, DeleteProduct

# Add namespace to urls
app_name = 'products'

urlpatterns = [
    path('', ListProduct.as_view(), name='list-products'),
    path('<uuid:product_id>/', DetailProduct.as_view(), name='detail-product'),
    path('create/', CreateProduct.as_view(), name='create-product'),
    path('<uuid:product_id>/edit/', EditProduct.as_view(), name='edit-product'),
    path('<uuid:product_id>/delete/', DeleteProduct.as_view(), name='delete-product'),
]



