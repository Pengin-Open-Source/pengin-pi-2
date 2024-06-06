from models import BlogPost
from util import paginate  # Assuming you have a pagination utility
# Define the blog post view
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import user_passes_test


# Define the blog view
def blogs(request):
    if request.method == "POST":
        page = int(request.POST.get('page_number', 1))
    else:
        page = 1

    # Use your custom paginate function
    posts = paginate(BlogPost, page=page, key="title", pages=10)

    # Check if the user is a staff member (admin)
    is_admin = user_passes_test(lambda u: u.is_staff)(request.user)
    
    return render(request, 'blogs.html', {
        'posts': posts,
        'primary_title': 'Blog',
        'is_admin': is_admin,
        'left_title': 'Blog Posts'
    })

def post(request, post_id):
    post = get_object_or_404(BlogPost, pk=post_id)
    
    if request.method == "POST":
        page = int(request.POST.get('page_number', 1))
    else:
        page = 1
    
    posts = paginate(BlogPost.objects.all(), page=page, key="title", per_page=10)
    author_date = post.date  # TODO: Replace with correct attribute
    is_admin = user_passes_test(lambda u: u.is_staff)(request.user)
    
    return render(request, 'post.html', {
        'page': page,
        'post': post,
        'posts': posts,
        'is_admin': is_admin,  # Assuming you have authentication
        'blog_author_date': author_date,
    })