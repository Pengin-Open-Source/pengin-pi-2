from django.urls import path
from .views import home, home_create, home_edit


urlpatterns = [
    path('', home, name='home'),
    path('home/', home, name='home'),
    path('index/', home, name='home'),
    path('index.html', home, name='home'),
    path('home/edit/', home_edit, name='home_edit'),
    path('home/create/', home_create, name='home_create'),
    ]



