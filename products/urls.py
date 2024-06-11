from django.urls import path
from .views import product_list, product_detail, create_edit_product

# Add namespace to urls
app_name = 'products'

urlpatterns = [
    path('', product_list, name='list-products'),
    path('<uuid:product_id>/', product_detail, name='detail-product'),
    # path('delete/<int:product_id>/', delete_product, name='delete_product'),
    path('create/', create_edit_product, name='create-product'),
    path('<uuid:product_id>/edit/', create_edit_product, name='edit-product'),
    # path('<int:product_id>/add_image/', add_image, name='add_image'),
]



