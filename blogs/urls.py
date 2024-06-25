from django.urls import path
from blogs.views import blogs, post, create_post, edit_post

app_name = 'blogs'

urlpatterns = [
    path('blog', blogs, name='blogs'),
    path('blogs', blogs, name='blogs'),
    path('blogs.html', blogs, name='blogs'),
    path('blogs/<uuid:post_id>/', post, name='blog_post'),
    path('blogs/<uuid:post_id>/edit/', edit_post, name='edit_blog_post'),
    path('blogs/create/', create_post, name='create_blog_post'),
]
