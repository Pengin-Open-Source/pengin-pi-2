from django.urls import path
from .views import products, product

urlpatterns = [
    path('products', products, name='products'),
    path('products.html', products, name='products'),
    path('products/<int:product_id>/', product, name='product'),
]



