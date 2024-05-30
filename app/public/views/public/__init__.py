from django.http import HttpResponse, HttpRequest
from models import BlogPost, Product
from util import paginate  # Assuming you have a pagination utility
# Define the blog post view
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from app.util.s3 import conn


# Define the home view
def home(request):
    return render(request, 'home.html')

# Define the about view
def about(request):
    return render(request, 'about.html')

# Define the blog view
def blogs(request):
    if request.method == "POST":
        page = int(request.POST.get('page_number', 1))
    else:
        page = 1

    # Use your custom paginate function
    posts = paginate(BlogPost, page=page, key="title", pages=10)

    # Check if the user is a staff member (admin)
    is_admin = user_passes_test(lambda u: u.is_staff)(request.user)
    
    return render(request, 'blogs.html', {
        'posts': posts,
        'primary_title': 'Blog',
        'is_admin': is_admin,
        'left_title': 'Blog Posts'
    })

def post(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id)
    
    if request.method == "POST":
        page = int(request.POST.get('page_number', 1))
    else:
        page = 1
    
    posts = paginate(BlogPost.objects.all(), page=page, key="title", per_page=10)
    author_date = post.date  # TODO: Replace with correct attribute
    is_admin = user_passes_test(lambda u: u.is_staff)(request.user)
    
    return render(request, 'post.html', {
        'page': page,
        'post': post,
        'posts': posts,
        'is_admin': is_admin,  # Assuming you have authentication
        'blog_author_date': author_date,
    })


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

    return render(request, "products/products.html", {
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

    return render(request, "products/product.html", {
        "is_admin": is_admin,
        "product": product,
        "page": 1,
        "primary_title": product.name,
    })

# Define the jobs view
def jobs(request):
    return render(request, 'jobs.html')

# Define the job view
def job(request, id):
    return render(request, 'job.html')
