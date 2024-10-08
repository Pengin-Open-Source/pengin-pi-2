from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from util.security.auth_tools import is_admin_required #, is_admin_provider, user_group_provider
from blogs.forms import BlogForm
from blogs.models import BlogPost, BlogHistory, transaction
from main.models.users import User
# Assuming you have a pagination utility
# Define the blog post view


# Define the blog view

'''
TODO: Remove user and roles.  We are not checking authors or usernames, nor roles.  
Just use is_admin_provider to send is_admin to views and lock down methods that require admin with the is_admin decorator.
These classes and methods are overly complicated, I'm not going to try to fix them, I would start over.

'''


class BlogsListView(ListView):
    queryset = BlogPost.objects.all()
    template_name = 'blogs.html'
    model = BlogPost
    context_object_name = 'blog_posts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_admin = self.request.user.is_authenticated and self.request.user.validated and self.request.user.is_staff
        context['is_admin'] = is_admin
        context['left_title'] = 'Blog Posts'
        context['primary_title'] = 'Blog'
        blog_posts = self.queryset.order_by('date')
        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        context['page_number'] = page_number
        paginator = Paginator(blog_posts, 10)
        posts = paginator.get_page(page_number)
        context['posts'] = posts
        return context


class BlogPostDetailView(DetailView):
    model = BlogPost
    template_name = 'blogpost.html'
    form_class = BlogForm
    context_object_name = 'blog_post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # perhaps this should be refactored to use self.object instead?
        blog_post = get_object_or_404(BlogPost, pk=self.kwargs.get('pk'))

        edit_info = get_last_edit_info(blog_post)
        #author_id, create_date, is_create_missing = author_info
        

        if edit_info:
            edited_date = edit_info
            #edited_by = User.objects.get(id=edited_by_id).name
        else:
            edited_date = ''
            #edited_by = ''

        blog_posts = BlogPost.objects.all().order_by('date')
        paginator = Paginator(blog_posts, 10)

        page = self.request.GET.get("page", 1)
        posts = paginator.get_page(page)
        is_admin = self.request.user.is_authenticated and self.request.user.validated and self.request.user.is_staff

        context['posts'] = posts
        context['post'] = blog_post
        #context['is_create_missing'] = is_create_missing
        #context['author'] = author
        #context['blog_author_date'] = create_date
        #context['edited_by'] = edited_by
        context['blog_edited_date'] = edited_date
        context['page'] = page
        context['is_admin'] = is_admin   # Assuming you have authentication
        return context


@method_decorator(is_admin_required, name='dispatch')
class BlogPostCreateView(LoginRequiredMixin, CreateView):

    model = BlogPost
    form_class = BlogForm
    template_name = 'create_blog_post.html'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        form = BlogForm(request.POST)
        if form.is_valid():
            # add these fields to the form
            blog_post = form.save(commit=False)
            blog_post.method = 'CREATE'
            #blog_post.user = request.user
            # date will be auto-filled by data model with "now"

            # this should just save a blank '[]' if there are no groups
            #query_groups = request.user.groups.all()
            #blog_post.roles = list(query_groups.values('pk', 'name'))
            # note comment over equivalent line in Blog Post Deletion
            #blog_post.roles.append({"pk": -2, "name": "STAFF"})
            blog_post.save()
            return HttpResponseRedirect(reverse_lazy('blogs:blog_post', kwargs={'pk': blog_post.id}))

    def get(self, request, *args, **kwargs):
        form = BlogForm()
        form_rendered_for_create = form.render("configure_blog_form.html")
        return render(request, self.template_name, {'form': form_rendered_for_create, 'is_admin': True})


@method_decorator(is_admin_required, name='dispatch')
class BlogPostEditView(LoginRequiredMixin, UpdateView):
    model = BlogPost
    form_class = BlogForm
    template_name = 'edit_blog_post.html'
    context_object_name = 'blog_post'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        post_id = self.kwargs.get('pk')
        blog_post = get_object_or_404(BlogPost, id=post_id)
        form = BlogForm(request.POST, instance=blog_post)
        if form.is_valid():
            blog_post = form.save(commit=False)
            # specify this is an edited record
            blog_post.method = 'EDIT'
            #blog_post.user = request.user
            blog_post.date = timezone.now()
            #query_groups = request.user.groups.all()
            #blog_post.roles = list(query_groups.values('pk', 'name'))
            # note comment over equivalent line in Blog Post Deletion
            #blog_post.roles.append({"pk": -2, "name": "STAFF"})
            blog_post.save()
            return HttpResponseRedirect(reverse_lazy('blogs:blog_post', kwargs={'pk': post_id}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # perhaps should be refactored to use self.object?
        blog_post = get_object_or_404(BlogPost, pk=self.kwargs.get('pk'))
        form = BlogForm(instance=blog_post)
        form_rendered_for_edit = form.render(
            "configure_blog_form.html")
        context['form'] = form_rendered_for_edit
        context['is_admin'] = True
        context['pk'] = self.kwargs.get('pk')
        return context


@method_decorator(is_admin_required, name='dispatch')
class BlogPostDeleteView(LoginRequiredMixin, DeleteView):
    model = BlogPost

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        post_id = self.kwargs.get('pk')
        blog_post = get_object_or_404(BlogPost, id=post_id)
        blog_post.method = 'DELETE'
        #blog_post.user = request.user
        blog_post.date = timezone.now()
        #query_groups = request.user.groups.all()
        #blog_post.roles = list(query_groups.values('pk', 'name'))
        # Since at this point only Staff can perform Deletes,  append the
        # Staff role for our records.
        # (Note the negative pk,  which will never exist as an id -
        # - no Staff group exists at this point,  but we want to note
        # that a Staff member did this.
        #blog_post.roles.append({"pk": -2, "name": "STAFF"})
        with transaction.atomic():
            blog_post.save()
            blog_post.delete()
        return HttpResponseRedirect(reverse_lazy('blogs:blogs'))


# utility methods
def get_create_info(blog_post):
    author = ''
    oldest_date = ''
    is_create_missing = False
    if blog_post.method == 'CREATE':
        #author = blog_post.user.id
        oldest_date = blog_post.date

    else:
        blog_post_history = BlogHistory.objects.filter(
            post_id=blog_post.id,  method="CREATE")
        # there should be only one value.
        # we will set a flag if there is no row with method 'CREATE'  in blog history
        oldest_post = blog_post_history.first()
        if oldest_post:
            #author = oldest_post.user
            oldest_date = oldest_post.date
        else:
            # DBAs TAKE NOTE: If a DBA archives or deleted some older blog history
            # then the row with the blog creation date/original post author could have
            # been deleted and will not be available now!
            is_create_missing = True
            author = 'NOT FOUND'
            oldest_date = 'DATE NOT FOUND'

    return (author, oldest_date, is_create_missing)


def get_last_edit_info(blog_post):
    if blog_post.method != 'CREATE':

        if blog_post.method == 'EDIT':
            # Last edit information is already in blog_post
            edit_date = blog_post.date
            #last_edit_user = blog_post.user.id
        elif blog_post.method == 'DELETE':
            # Likely means A DBA restored a deleted row from history,  with the latest history record,
            # which would have method value: 'DELETE'.
            # (It's preferable to get the first history row with 'EDIT' instead)
            # So, get the first Blog history row with method = 'EDIT'
            blog_post_history = BlogHistory.objects.filter(
                post_id=blog_post.id, method="EDIT")
            last_edit = blog_post_history.order_by("-date").first()
            edit_date = last_edit.date
            #last_edit_user = last_edit.user

        return (edit_date)
    # If row was just created,  no edit information is available.
    return None
