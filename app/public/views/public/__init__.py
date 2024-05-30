from django.http import HttpResponse, HttpRequest
from models import BlogPost, Product, Job, Home, About
from util import paginate  # Assuming you have a pagination utility
# Define the blog post view
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from app.util.s3 import conn
from django.conf import settings
from botocore.exceptions import ParamValidationError
from app.util.defaults import default
import logging


# Define the home view
def home(request):
    home = Home.objects.first() or default.Home()
    is_admin = user_passes_test(lambda u: u.is_staff)(request.user)
    try:
        image = conn.get_URL(home.image)
    except ParamValidationError:
        image = default.image

    if home:
        logging.info("S3 Image accessed: " + home.image)

    return render(request, "home.html", {
        'is_admin': is_admin,
        'home': home,
        'image': image
    })

# Define the about view
def about(request):
    about = About.objects.first() or default.About()
    is_admin = user_passes_test(lambda u: u.is_staff)(request.user)
    try:
        image = conn.get_URL(about.image)
    except ParamValidationError:
        image = default.image

    if about:
        logging.info("Image S3 URL accessed:" + about.image)

    return render(request, "about.html", {
        'about': about,
        'is_admin': is_admin,
        'image': image,
        'primary_title': "About Us"
    })

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

# Define the jobs view
def jobs(request: HttpRequest):
    jobs_per_page = 9
    if request.method == 'POST':
        page = int(request.POST.get('page_number', 1))
    else:
        page = 1

    jobs_paginated = paginate(Job, page=page, key='job_title', pages=jobs_per_page)
    is_admin = user_passes_test(lambda u: u.is_staff)(request.user)
    
    return render(request, 'jobs.html', {
        'is_admin': is_admin,
        'jobs': jobs_paginated,
        'page': page,
        'primary_title': 'Jobs',
    })

# Define the job view
def job(request: HttpRequest, job_id: int):
    job = get_object_or_404(Job, id=job_id)

    applications = job.applications.all()
    user_applied = applications.filter(user_id=request.user.id).exists()
    user_application_id = applications.filter(user_id=request.user.id).values_list('id', flat=True).first()
    is_admin = user_passes_test(lambda u: u.is_staff)(request.user)
    
    return render(request, 'job.html', {
        'is_admin': is_admin,
        'job': job,
        'applications': applications,
        'user_applied': user_applied,
        'user_application_id': user_application_id,
        'page': 1,
        'primary_title': job.job_title,
    })