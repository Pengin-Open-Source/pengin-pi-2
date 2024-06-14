from blogs.models import BlogPost
from util.paginate import paginate  # Assuming you have a pagination utility
# Define the blog post view
from django.shortcuts import render, get_object_or_404
from util.security.auth_tools import is_admin_provider


# Define the blog view
@is_admin_provider
def blogs(request, is_admin):
    if request.method == "POST":
        page = int(request.POST.get('page_number', 1))
    else:
        page = 1
    # Use your custom paginate function
    posts = paginate(BlogPost.objects.all, page=page, key="-date", per_page=10)

    return render(request, 'blogs.html', {
        'posts': posts,
        'primary_title': 'Blog',
        'is_admin': is_admin,
        'left_title': 'Blog Posts'
    })


@is_admin_provider
def post(request, post_id, is_admin):
    post = get_object_or_404(BlogPost, pk=post_id)

    if request.method == "POST":
        page = int(request.POST.get('page_number', 1))
    else:
        page = 1

    posts = paginate(BlogPost.objects.all(), page=page,
                     key="title", per_page=10)
    author_date = post.date  # TODO: Replace with correct attribute

    return render(request, 'post.html', {
        'page': page,
        'post': post,
        'posts': posts,
        'is_admin': is_admin,  # Assuming you have authentication
        'blog_author_date': author_date,
    })
