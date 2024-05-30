"""
URL configuration for Pengin-Pi 2 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from public.views.public import home, about, blog, products, jobs

urlpatterns = [
    path('', home, name='home'),
    path('home', home, name='home'),
    path('index', home, name='home'),
    path('index.html', home, name='home'),
    path('about', about, name='about'),
    path('about.html', about, name='about'),
    path('blog', blog, name='blog'),
    path('blog.html', blog, name='blog'),
    path('products', products, name='products'),
    path('products.html', products, name='products'),
    path('jobs', jobs, name='jobs'),
    path('jobs.html', jobs, name='jobs'),
]



