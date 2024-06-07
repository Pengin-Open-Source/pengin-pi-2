from django.urls import path
from .views import products, product, create_product

urlpatterns = [
    path('products', products, name='products'),
    path('products.html', products, name='products'),
    path('products/<int:product_id>/', product, name='product'),
    path('create/', create_product, name='create_product'),
]



