from django.http import HttpResponse
from django.shortcuts import render


# Define the home view
def home(request):
    return render(request, 'home.html')

# Define the about view
def about(request):
    return render(request, 'about.html')

# Define the blog view
def blog(request):
    return render(request, 'blog.html')

# Define the products view
def products(request):
    return render(request, 'products.html')

# Define the jobs view
def jobs(request):
    return render(request, 'jobs.html')
