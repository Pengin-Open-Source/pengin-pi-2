from django.urls import path
from public.views import home

urlpatterns = [
    path('', home, name='home'),
    path('home', home, name='home'),
    path('index', home, name='home'),
    path('index.html', home, name='home'),
]
