# forums/urls.py
from django.urls import path
from .views import (
    ForumsListView, ThreadCreateView, ThreadDetailView, 
    PostCreateView, PostDetailView, PostEditView, 
    ThreadDeleteView, PostDeleteView, CommentEditView, CommentDeleteView
)

urlpatterns = [
    path('', ForumsListView.as_view(), name='forums'),
    path('create/', ThreadCreateView.as_view(), name='create_thread'),
    path('<uuid:pk>/', ThreadDetailView.as_view(), name='thread'),
    path('<uuid:thread_id>/create/', PostCreateView.as_view(), name='create_post'),
    path('<uuid:thread_id>/<uuid:pk>/', PostDetailView.as_view(), name='post'),
    path('<uuid:thread_id>/<uuid:pk>/edit/', PostEditView.as_view(), name='edit_post'),
    path('<uuid:thread_id>/<uuid:post_id>/<uuid:pk>/edit/', CommentEditView.as_view(), name='edit_comment'),
    path('delete/thread/<uuid:pk>/', ThreadDeleteView.as_view(), name='delete_thread'),
    path('delete/post/<uuid:pk>/', PostDeleteView.as_view(), name='delete_post'),
    path('delete/comment/<uuid:pk>/', CommentDeleteView.as_view(), name='delete_comment'),
]
