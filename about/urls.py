from django.urls import path
from .views import AboutView, AboutEdit, AboutCreate

urlpatterns = [
    path('about/', AboutView.as_view(), name='about_view'),
    path('about/edit/', AboutEdit.as_view(), name='about_edit'),
    path('about/create/', AboutCreate.as_view(), name='about_create'),
    ]