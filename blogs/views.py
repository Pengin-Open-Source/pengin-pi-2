from blogs.models import BlogPost
from django.core.paginator import Paginator
from util.paginate import paginate  # Assuming you have a pagination utility
# Define the blog post view
from django.shortcuts import render, redirect, get_object_or_404
from util.security.auth_tools import is_admin_provider
from django.contrib.auth.decorators import login_required
from blogs.forms import BlogForm
# Define the blog view


@is_admin_provider
def blogs(request, is_admin):
    if request.method == "POST":
        page = int(request.POST.get('page_number', 1))
    else:
        page = 1

    blog_posts = BlogPost.objects.all().order_by('date')
    paginator = Paginator(blog_posts, 10)

    posts = paginator.get_page(page)
    print(posts)

    return render(request, 'blogs.html', {
        'posts':  posts,
        'primary_title': 'Blog',
        'is_admin': is_admin,  # Can I remove this now that we have is_admin_provider?
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


@is_admin_provider
def create_post(request, is_admin):
    if request.method == 'POST':
        form = BlogForm(request.POST)
        if form.is_valid():
            # add these fields to the form
            form.set_cleaned_data_field('method', 'CREATE')
            blog_post = form.save()
            return render(request, 'success.html')
        else:
            return render(request, 'create_blog_post.html', {'form': form, 'is_admin': is_admin})
    else:

        prefill_data = {'author': request.user.name}
        remove_fields = ['edited_by']
        form = BlogForm(remove_fields=remove_fields, prefill_data=prefill_data)

        form_rendered_for_create = form.render(
            "configure_form_for_create.html")
        return render(request, 'create_blog_post.html', {'form': form_rendered_for_create, 'is_admin': is_admin})
