from django.urls import path
from .views import products, product, create_product

# Add namespace to urls
app_name = 'products'

urlpatterns = [
    path('', products, name='products'),
    path('<int:product_id>/', product, name='product'),
    path('create/', create_product, name='create_product'),
    # path('edit/<int:product_id>/', edit_product, name='edit_product'),
    # path('delete/<int:product_id>/', delete_product, name='delete_product'),
    # path('<int:product_id>/add_image/', add_image, name='add_image'),
]



