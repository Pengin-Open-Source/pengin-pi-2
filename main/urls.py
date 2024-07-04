"""
URL configuration for main project.

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
from django.contrib import admin
from django.urls import path, include
from .views import LoginView, SignupView, LogoutView, PasswordResetRequestView, PasswordResetView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('', include('about.urls')),
    path('', include('blogs.urls')),
    path('', include('applications.urls')),
    path('products/', include('products.urls')),
    path('', include('jobs.urls')),
    path('forums/', include('forums.urls')),
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('generate-prt/', PasswordResetRequestView.as_view(), name='generate_prt'),
    path('reset-password/<str:token>/', PasswordResetView.as_view(), name='reset_password'),
]
