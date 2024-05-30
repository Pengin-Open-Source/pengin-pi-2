from django.http import HttpResponse
from django.shortcuts import render


# Define the home view
def home(request):
    return render(request, 'home.html')

# Define the about view
def about(request):
    return render(request, 'about.html')

# Define the blog view
def blogs(request):
    return render(request, 'blogs.html')

# Define the blog post view
def post(request, id):
    return render(request, 'post.html')

# Define the products view
def products(request):
    return render(request, 'products.html')

# Define the product view
def product(request, id):
    return render(request, 'product.html')

# Define the jobs view
def jobs(request):
    return render(request, 'jobs.html')

# Define the job view
def job(request, id):
    return render(request, 'job.html')
