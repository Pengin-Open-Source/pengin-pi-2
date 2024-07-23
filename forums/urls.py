# forums/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.forums, name='forums'),
    path('create/', views.create_thread, name='create_thread'),
    path('<uuid:thread_id>/', views.thread, name='thread'),
    path('<uuid:thread_id>/create/', views.create_post, name='create_post'),
    path('<uuid:thread_id>/<uuid:post_id>/', views.post, name='post'),
    path('<uuid:thread_id>/<uuid:post_id>/edit/', views.edit_post, name='edit_post'),
    path('<uuid:thread_id>/<uuid:post_id>/<uuid:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('delete/thread/<uuid:id>/', views.delete_thread, name='delete_thread'),
    path('delete/post/<uuid:id>/', views.delete_post, name='delete_post'),
    path('delete/comment/<uuid:id>/', views.delete_comment, name='delete_comment'),
]
