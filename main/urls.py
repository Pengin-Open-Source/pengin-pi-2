# main/urls.py
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
    path('orders/', include('orders.urls.orders')),
    path('customers/', include('orders.urls.customers')),
    path('contracts/', include('contracts.urls')),
    path('', include('jobs.urls')),
    path('tickets/', include('tickets.urls')),
    path('forums/', include('forums.urls')),
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('generate-prt/', PasswordResetRequestView.as_view(), name='generate_prt'),
    path('reset-password/<str:token>/', PasswordResetView.as_view(), name='reset_password'),
    path('profile/', include('profiles.urls')), 
]
