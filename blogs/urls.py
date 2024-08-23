from django.urls import path
from blogs.views import BlogsListView, post, create_post, edit_post, delete_post

app_name = 'blogs'

urlpatterns = [
    path('blog', BlogsListView.as_view(), name='blogs'),
    path('blogs', BlogsListView.as_view(), name='blogs'),
    path('blogs.html', BlogsListView.as_view(), name='blogs'),
    path('blogs/<uuid:post_id>/', post, name='blog_post'),
    path('blogs/<uuid:post_id>/edit/', edit_post, name='edit_blog_post'),
    path('blogs/<uuid:post_id>/delete/', delete_post, name='delete_blog_post'),
    path('blogs/create/', create_post, name='create_blog_post'),
]
