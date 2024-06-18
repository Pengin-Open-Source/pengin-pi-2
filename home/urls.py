from django.urls import path
from .views import HomeView, HomeCreate, HomeEdit


urlpatterns = [
    path('', HomeView.as_view(), name='home_view'),
    path('home/edit/', HomeEdit.as_view(), name='home_edit'),
    path('home/create/', HomeCreate.as_view(), name='home_create'),
    path('home/', HomeView.as_view(), name='home_view'),
    path('index/', HomeView.as_view(), name='home_view'),
    path('index.html', HomeView.as_view(), name='home_view'),
    ]



