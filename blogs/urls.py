from django.urls import path
from blogs.views import blogs, post, create_post

urlpatterns = [
    path('blog', blogs, name='blogs'),
    path('blogs.html', blogs, name='blogs'),
    path('blogs/<int:post_id>/', post, name='blog_post'),
    path('blog/create/', create_post, name='create_blog_post'),
]
