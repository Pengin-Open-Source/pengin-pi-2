from django.http import HttpRequest
from .models import Product
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from botocore.exceptions import ParamValidationError
from util.s3 import File
from util.security.auth_tools import is_admin_provider, is_admin_required
from .forms import ProductForm
from werkzeug.utils import secure_filename

conn = File()


@is_admin_required
def create_edit_product(request, product_id=None):
    context = {}
    # Check if product_id is provided: if so, get and edit the product
    if product_id:
        product = get_object_or_404(Product, id=product_id)
        try:
            product.card_image_url = conn.get_URL(product.card_image_url)
        except ParamValidationError:
            product.card_image_url = None
        try:
            product.stock_image_url = conn.get_URL(product.stock_image_url)
        except ParamValidationError:
            product.stock_image_url = None

        context["card_image_url"] = product.card_image_url
        context["stock_image_url"] = product.stock_image_url

        # If the request method is POST, create a form with the request data and the product instance
        if request.method == "POST":
            form = ProductForm(request.POST, request.FILES, instance=product)
        # If the request method is GET, create a form with the product instance
        else:
            form = ProductForm(instance=product)
        context["primary_title"] = f'Edit Product: {product.name}'
        context["action"] = "update"

    # Create a new product
    else:
        # If the request method is POST, create a form with the request data
        if request.method == "POST":
            form = ProductForm(request.POST, request.FILES)
        # If the request method is GET, create a blank form
        else:
            form = ProductForm()
        context["primary_title"] = "Create Product"
        context["action"] = "create"

    context["form"] = form

    # If the request method is POST and the form is valid, save the product
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)

        large_file = request.FILES.get('file_large')
        small_file = request.FILES.get('file_small')

        if large_file:
            large_file.filename = secure_filename(large_file.name)
            product.stock_image_url = conn.create(large_file)

        if small_file:
            small_file.filename = secure_filename(small_file.name)
            product.card_image_url = conn.create(small_file)

        product.save()
        return redirect('products:detail-product', product_id=product.id)

    return render(request, "product_form.html", context)


# List all products with pagination
@is_admin_provider
def product_list(request, is_admin):
    products = Product.objects.all().order_by("priority")
    for product in products:
        try:
            product.card_image_url = conn.get_URL(product.card_image_url)
        except ParamValidationError:
            product.card_image_url = None

    paginator = Paginator(products, 9)
    page_number = request.GET.get("page", 1)
    page_products = paginator.get_page(page_number)

    return render(request, "products.html", {
        "is_admin": is_admin,
        "page_products": page_products,
        "primary_title": "Products",
    })


# Display product details
@is_admin_provider
def product_detail(request, product_id, is_admin):
    product = get_object_or_404(Product, id=product_id)
    try:
        product.stock_image_url = conn.get_URL(product.stock_image_url)
    except ParamValidationError:
        product.stock_image_url = None

    return render(request, "product.html", {
        "is_admin": is_admin,
        "product": product,
        "primary_title": product.name,
    })


@is_admin_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        return redirect('products:list-products')

    return render(request, 'product_confirm_delete.html', {'product': product})

