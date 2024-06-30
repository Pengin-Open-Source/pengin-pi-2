from blogs.models import BlogPost, BlogHistory, transaction
from django.core.paginator import Paginator
from main.models.users import User
from util.paginate import paginate  # Assuming you have a pagination utility
# Define the blog post view
from django.shortcuts import render, redirect, get_object_or_404
from util.security.auth_tools import is_admin_provider, user_group_provider
from django.contrib.auth.decorators import login_required
from blogs.forms import BlogForm
from django.utils import timezone


# Define the blog view


@is_admin_provider
def blogs(request, is_admin):
    page = request.GET.get("page", 1)

    blog_posts = BlogPost.objects.all().order_by('date')
    paginator = Paginator(blog_posts, 10)
    posts = paginator.get_page(page)

    return render(request, 'blogs.html', {
        'posts':  posts,
        'page': page,
        'primary_title': 'Blog',
        'is_admin': is_admin,
        'left_title': 'Blog Posts'
    })


@is_admin_provider
def post(request, post_id, is_admin):
    blog_post = get_object_or_404(BlogPost, pk=post_id)

    author_date = get_create_date(blog_post.id)
    edit_info = get_last_edit_info(blog_post.id)

    if edit_info:
        edited_date, edited_by = edit_info
    else:
        edited_date = ''
        edited_by = ''

    blog_posts = BlogPost.objects.all().order_by('date')
    paginator = Paginator(blog_posts, 10)

    page = request.GET.get("page", 1)
    posts = paginator.get_page(page)

    return render(request, 'post.html', {
        'posts': posts,
        'post': blog_post,
        'author': blog_post.author,
        'blog_edited_date': edited_date,
        'edited_by': edited_by,
        'page': page,
        'is_admin': is_admin,  # Assuming you have authentication
        'blog_author_date': author_date,
    })


@login_required
@is_admin_provider
@user_group_provider
def create_post(request, is_admin, groups):
    if request.method == 'POST':
        form = BlogForm(request.POST)
        if form.is_valid():
            # add these fields to the form
            blog_post = form.save(commit=False)
            blog_post.method = 'CREATE'
            blog_post.user = request.user
            # date will be auto-filled by data model with "now"
            qs = request.user.groups.all()
            blog_post.roles = list(qs.values('pk', 'name'))
            blog_post.save()
            return redirect('blogs:blog_post', post_id=blog_post.id)
        else:
            return render(request, 'create_blog_post.html', {'form': form, 'is_admin': is_admin})
    else:

        prefill_data = {'author': request.user.name}
        remove_fields = ['edited_by']
        form = BlogForm(remove_fields=remove_fields, prefill_data=prefill_data)

        form_rendered_for_create = form.render("configure_blog_form.html")
        return render(request, 'create_blog_post.html', {'form': form_rendered_for_create, 'is_admin': is_admin})


@login_required
@is_admin_provider
@user_group_provider
def edit_post(request, post_id, is_admin, groups):
    if request.method == 'POST':
        blog_post = get_object_or_404(BlogPost, id=post_id)
        form = BlogForm(request.POST, instance=blog_post)
        if form.is_valid():
            blog_post = form.save(commit=False)
            # specify this is an edited record
            blog_post.method = 'EDIT'
            user = User.objects.get(pk=request.user.id)
            print(type(user))
            blog_post.user = user  # Assign the complete User object
            # blog_post.user = User.objects.get(pk=request.user.id)
            blog_post.date = timezone.now()
            qs = request.user.groups.all()
            blog_post.roles = list(qs.values('pk', 'name'))
            print("blog post user is: ")
            print(blog_post.user)
            blog_post.save()
            return redirect('blogs:blog_post', post_id=blog_post.id)
        else:
            return render(request, 'edit_blog_post.html', {'form': form, 'is_admin': is_admin, 'post_id': post_id})
    else:
        blog_post = get_object_or_404(BlogPost, id=post_id)
        prefill_data = {'edited_by': request.user.name}
        form = BlogForm(prefill_data=prefill_data,  instance=blog_post)

        form_rendered_for_edit = form.render(
            "configure_blog_form.html")
        return render(request, 'edit_blog_post.html',  {'form': form_rendered_for_edit, 'is_admin': is_admin,  'post_id': post_id})


@login_required
@is_admin_provider
@user_group_provider
def delete_post(request, post_id, is_admin, groups):
    blog_post = get_object_or_404(BlogPost, id=post_id)
    blog_post.method = 'DELETE'
    blog_post.user = request.user
    blog_post.date = timezone.now()
    blog_post.roles = groups
    with transaction.atomic():
        # specify this is an deleted record
        # both save and delete must execute or fail together,
        # since we are saving changes to history first.
        # this keeps track of the time of deletion and
        # the user who deleted the record
        blog_post.save()
        blog_post.delete()
        # if successful return to main blog post
    return redirect('blogs:blogs')


# utility methods
def get_create_date(post_id):
    blog_post_history = BlogHistory.objects.filter(post_id=post_id)
    # The oldest date should be the date of blog post creation
    if blog_post_history:
        # could be many dates in Blog History table for a given
        # post_id if there are many edits
        oldest_date = blog_post_history.order_by("date").first().date
    else:
        # This should only have one post, so first is
        newly_created_post = BlogPost.objects.get(id=post_id)
        oldest_date = newly_created_post.date
    return oldest_date


def get_last_edit_info(post_id):
    blog_post_history = BlogHistory.objects.filter(
        post_id=post_id, method="EDIT")
    # The newest date should be the date of the last blog post edit
    if blog_post_history:
        last_edit = blog_post_history.order_by("-date").first()
        return (last_edit.date, last_edit.user)
    return None
