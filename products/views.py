from django.http import HttpRequest
from .models import Product
from django.core.paginator import Paginator
# Define the blog post view
from django.shortcuts import render, get_object_or_404, redirect
from util.s3 import File
from util.security.auth_tools import is_admin_provider, is_admin_required
from .forms import ProductForm
from werkzeug.utils import secure_filename
# views.py

conn = File()


@is_admin_required
def create_product(request):
    form = ProductForm()

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
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

    return render(request, 'product_create.html', {'form': form, 'primary_title': "Create Product"})


# Define the products view
@is_admin_provider
def product_list(request, is_admin):
    products = Product.objects.all().order_by("priority")
    for prod in products:
        prod.card_image_url = conn.get_URL(prod.card_image_url)

    paginator = Paginator(products, 9)
    page_number = request.GET.get("page", 1)
    page_products = paginator.get_page(page_number)

    return render(request, "products.html", {
        "is_admin": is_admin,
        "page_products": page_products,
        "primary_title": "Products",
    })

# Define the product view
@is_admin_provider
def product_detail(request, product_id: int, is_admin):
    product = get_object_or_404(Product, id=product_id)
    product.stock_image_url = conn.get_URL(product.stock_image_url)
    
    return render(request, "product.html", {
        "is_admin": is_admin,
        "product": product,
        "page": 1,
        "primary_title": product.name,
    })
    
