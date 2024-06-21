from django.urls import path
from .views import HomeView, HomeCreate, HomeEdit
from django.shortcuts import redirect


urlpatterns = [
    path('', lambda request: redirect('home_view', permanent=True)),
    path('home/', HomeView.as_view(), name='home_view'),
    path('index/', lambda request: redirect('home_view', permanent=True)),
    path('index.html', lambda request: redirect('home_view', permanent=True)),
    path('home/edit/', HomeEdit.as_view(), name='home_edit'),
    path('home/create/', HomeCreate.as_view(), name='home_create'),
    ]