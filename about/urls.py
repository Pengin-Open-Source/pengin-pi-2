from django.urls import path
from .views import about, edit_about, create_about

urlpatterns = [
    path('about', about, name='about'),
    path('about.html', about, name='about'),
    path('about/edit/', edit_about, name='edit_about'),
    path('about/create/', create_about, name='create_about'),
]