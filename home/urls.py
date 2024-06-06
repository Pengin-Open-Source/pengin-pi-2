from django.urls import path
from public.views.public import home, about, blogs, post, products, jobs, product, job

urlpatterns = [
    path('', home, name='home'),
    path('home', home, name='home'),
    path('index', home, name='home'),
    path('index.html', home, name='home'),
    path('about', about, name='about'),
    path('about.html', about, name='about'),
    path('blogs', blogs, name='blogs'),
    path('blogs.html', blogs, name='blogs'),
    path('blogs/<int:post_id>/', post, name='post'),
    path('products', products, name='products'),
    path('products.html', products, name='products'),
    path('products/<int:product_id>/', product, name='product'),
    path('jobs', jobs, name='jobs'),
    path('jobs.html', jobs, name='jobs'),
    path('jobs/<int:job_id>/', job, name='job'),
]



