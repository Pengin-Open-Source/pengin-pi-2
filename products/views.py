from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
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


class CreateProduct(View):
    form = ProductForm()
    template_name = "product_form.html"
    context = {
        "primary_title": "Create Product",
        "action": "create",
        "form": form,
    }

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request):
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = save_product(request, form)
            return redirect('products:detail-product', product_id=product.id)
        self.context["form"] = form
        return render(request, self.template_name, self.context)


class EditProduct(View):
    template_name = "product_form.html"

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
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
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = save_product(request, form)
            return redirect('products:detail-product', product_id=product.id)
        return redirect('products:edit-product', product_id=product.id)


# List all products with pagination
class ListProduct(View):
    template_name = "products.html"

    @method_decorator(is_admin_provider)
    def get(self, request, is_admin):
        products = Product.objects.all().order_by("priority")
        for product in products:
            try:
                product.card_image_url = conn.get_URL(product.card_image_url)
            except ParamValidationError:
                product.card_image_url = None

        paginator = Paginator(products, 9)
        page_number = request.GET.get("page", 1)
        page_products = paginator.get_page(page_number)

        return render(request, self.template_name, {
            "is_admin": is_admin,
            "page_products": page_products,
            "primary_title": "Products",
        })


# Display product details
class DetailProduct(View):
    template_name = "product.html"

    @method_decorator(is_admin_provider)
    def get(self, request, product_id, is_admin):
        product = get_object_or_404(Product, id=product_id)
        try:
            product.stock_image_url = conn.get_URL(product.stock_image_url)
        except ParamValidationError:
            product.stock_image_url = None

        return render(request, self.template_name, {
            "is_admin": is_admin,
            "product": product,
            "primary_title": product.name,
        })


class DeleteProduct(View):
    template_name = "product_confirm_delete.html"

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        context = {
            "primary_title": f"Delete Product: {product.name}",
            "product": product,
        }
        return render(request, self.template_name, context)

    @method_decorator(login_required)
    @method_decorator(is_admin_required)
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        product.delete()
        return redirect('products:list-products')
