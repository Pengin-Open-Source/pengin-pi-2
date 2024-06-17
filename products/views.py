from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from botocore.exceptions import ParamValidationError
from werkzeug.utils import secure_filename
from .models import Product
from .forms import ProductForm
from util.s3 import File
from util.security.auth_tools import is_admin_provider, is_admin_required

conn = File()


def save_product(request, form):
    """
    Save the product to the database
    :param request: HttpRequest
    :param form: ProductForm
    :return: Product
    """
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
    return product


@login_required
@is_admin_required
def create_product(request):

    # If the request method is POST, create a form with the request data
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = save_product(request, form)
            return redirect('products:detail-product', product_id=product.id)

    # If the request method is GET, create a blank form
    form = ProductForm()

    context = {
        "primary_title": "Create Product",
        "action": "create",
        "form": form,
    }
    return render(request, "product_form.html", context)


@login_required
@is_admin_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # If the request method is POST, create a form with the request data and the product instance
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = save_product(request, form)
            return redirect('products:detail-product', product_id=product.id)

    # If the request method is GET, create a form with the product instance
    form = ProductForm(instance=product)

    try:
        product.card_image_url = conn.get_URL(product.card_image_url)
    except ParamValidationError:
        product.card_image_url = None
    try:
        product.stock_image_url = conn.get_URL(product.stock_image_url)
    except ParamValidationError:
        product.stock_image_url = None

    context = {
        "card_image_url": product.card_image_url,
        "stock_image_url": product.stock_image_url,
        "primary_title": f"Edit Product: {product.name}",
        "action": "update", "form": form,
        "product_id": product_id,
    }
    return render(request, "product_form.html", context)


# List all products with pagination
@login_required
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
@login_required
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


@login_required
@is_admin_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.delete()
        return redirect('products:list-products')

    context = {
        "primary_title": f"Delete Product: {product.name}",
        "product": product,
    }
    return render(request, 'product_confirm_delete.html', context)

