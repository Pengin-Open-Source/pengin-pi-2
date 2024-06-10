from django.urls import path
from .views import product_list, product_detail, create_product

# Add namespace to urls
app_name = 'products'

urlpatterns = [
    path('', product_list, name='list-products'),
    path('<int:product_id>/', product_detail, name='detail-product'),
    path('create/', create_product, name='create_product'),
    # path('edit/<int:product_id>/', edit_product, name='edit_product'),
    # path('delete/<int:product_id>/', delete_product, name='delete_product'),
    # path('<int:product_id>/add_image/', add_image, name='add_image'),
]



