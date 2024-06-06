from django.http import HttpRequest
from models import Product
from util import paginate  # Assuming you have a pagination utility
# Define the blog post view
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from util.s3 import conn


# Define the products view
def products(request: HttpRequest):
    if request.method == "POST":
        page = int(request.POST.get("page_number", 1))
    else:
        page = 1

    products = paginate(Product, page=page, key="name", pages=9)
    is_admin = user_passes_test(lambda u: u.is_staff)(request.user)
    for product in products:
        product.card_image_url = conn.get_URL(product.card_image_url)

    return render(request, "products.html", {
        "is_admin": is_admin,
        "products": products,
        "page": page,
        "primary_title": "Products",
    })

# Define the product view
def product(request: HttpRequest, product_id: int):
    product = get_object_or_404(Product, id=product_id)
    product.stock_image_url = conn.get_URL(product.stock_image_url)
    is_admin = user_passes_test(lambda u: u.is_staff)(request.user)

    return render(request, "product.html", {
        "is_admin": is_admin,
        "product": product,
        "page": 1,
        "primary_title": product.name,
    })