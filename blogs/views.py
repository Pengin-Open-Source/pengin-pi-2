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

    author_info = get_create_info(blog_post)
    edit_info = get_last_edit_info(blog_post)
    author, create_date, is_create_missing = author_info

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
        'is_create_missing': is_create_missing,
        'author': author,
        'blog_author_date': create_date,
        'edited_by': edited_by,
        'blog_edited_date': edited_date,
        'page': page,
        'is_admin': is_admin,  # Assuming you have authentication

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
            query_groups = request.user.groups.all()
            blog_post.roles = list(query_groups.values('pk', 'name'))
            blog_post.save()
            return redirect('blogs:blog_post', post_id=blog_post.id)
        else:
            return render(request, 'create_blog_post.html', {'form': form, 'is_admin': is_admin})
    else:
        form = BlogForm()

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
            blog_post.user = request.user
            blog_post.date = timezone.now()
            query_groups = request.user.groups.all()
            blog_post.roles = list(query_groups.values('pk', 'name'))
            blog_post.save()
            return redirect('blogs:blog_post', post_id=blog_post.id)
        else:
            return render(request, 'edit_blog_post.html', {'form': form, 'is_admin': is_admin, 'post_id': post_id})
    else:
        blog_post = get_object_or_404(BlogPost, id=post_id)
        form = BlogForm(instance=blog_post)

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
    query_groups = request.user.groups.all()
    blog_post.roles = list(query_groups.values('pk', 'name'))
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
def get_create_info(blog_post):
    author = ''
    oldest_date = ''
    is_create_missing = False
    if blog_post.method == 'CREATE':
        author = blog_post.user.name
        oldest_date = blog_post.date

    else:
        blog_post_history = BlogHistory.objects.filter(
            post_id=blog_post.id,  method="CREATE")
        # there should be only one value.
        # we should expect an error to be thrown here if there is no CREATE in blog history
        try:
            oldest_post = blog_post_history.first()
            author = oldest_post.user.name
            oldest_date = oldest_post.date
        except BlogHistory.DoesNotExist:
            is_create_missing = True

    return (author, oldest_date, is_create_missing)


def get_last_edit_info(blog_post):
    if blog_post.method != 'CREATE':

        if blog_post.method != 'EDIT':
            # Last edit information is already in blog_post
            last_edit = blog_post
        elif blog_post.method == 'DELETE':
            # Likely means A DBA restored a deleted row from history,  with the latest history record,
            # which would have method value: 'DELETE'.
            # (It's preferable to get the first history row with 'EDIT' instead)
            # So, get the first Blog history row with method = 'EDIT'
            blog_post_history = BlogHistory.objects.filter(
                post_id=post_id, method="EDIT")
            last_edit = blog_post_history.order_by("-date").first()

        return (last_edit.date, last_edit.user.name)
    # If row was just created,  no edit information is available.
    return None
