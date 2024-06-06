from django.urls import path
from .views import blogs, post

urlpatterns = [
    path('blog', blogs, name='blogs'),
    path('blogs.html', blogs, name='blogs'),
    path('blogs/<int:post_id>/', post, name='post'),
]



