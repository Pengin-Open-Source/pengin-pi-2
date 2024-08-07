from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from forums.models import Thread, ForumPost,  ForumPostHistory, ForumComment, ForumCommentHistory, ThreadRole, transaction
from forums.forms import ThreadForm, ForumPostForm, ForumCommentForm
from util.security.auth_tools import group_required, is_admin_required
from django.utils import timezone


from main.models.users import User


@method_decorator(group_required('user'), name='dispatch')
class ForumsListView(LoginRequiredMixin, ListView):

    queryset = Thread.objects.all()
    template_name = 'threads.html'
    model = Thread

    context_object_name = 'threads'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.request.user.is_staff
        context['primary_title'] = 'Forums'

        # If a staff user is requesting, get all forum threads.
        # otherwise, just get the threads
        # associated with a group the user is a part of.
        if self.request.user.is_staff:
            threads = self.queryset.order_by('name')
        else:
            user_groups = self.request.user.groups.all()
            threads = self.queryset.filter(
                groups__in=user_groups).order_by('name')

        # Similar to what Sincere is using for companies
        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(threads, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj

        return context


@method_decorator(group_required('user'), name='dispatch')
@method_decorator(is_admin_required, name='dispatch')
class ThreadCreateView(LoginRequiredMixin, CreateView):

    model = Thread
    form_class = ThreadForm
    template_name = 'create_thread.html'
    success_url = reverse_lazy('forums')

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        query_groups = Group.objects.all()
        roles = list(query_groups.values('id', 'name'))
        form = ThreadForm()
        context = {'roles': roles, 'form': form}
        return render(request, self.template_name,  context)

    def post(self, request):
        form = ThreadForm(request.POST)
        if form.is_valid():
            role = self.request.POST.get('role')
            form.instance.user = self.request.user
            form.instance.row_action = 'CREATE'
            selected_role = Group.objects.get(pk=role)
            form.instance.group = selected_role
            thread = form.save()
            ThreadRole.objects.create(thread=thread, group=selected_role)
            return HttpResponseRedirect(reverse_lazy('thread', kwargs={'pk': form.instance.pk}))


@method_decorator(group_required('user'), name='dispatch')
class ThreadDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Thread
    template_name = 'thread.html'
    context_object_name = 'thread'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = self.object.posts.all().order_by('-date')
        for forum_post in posts:
            if forum_post.row_action == 'CREATE':
                forum_post.is_create_missing = False
                forum_post.author = forum_post.user
            else:
                post_creation_info = get_post_create_info(forum_post)
                post_author_id, forum_post.create_date, forum_post.is_create_missing = post_creation_info
                if post_author_id != 'NOT FOUND':
                    post_author = User.objects.get(id=post_author_id)
                else:
                    post_author = 'NOT FOUND'
                forum_post.author = post_author

        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(posts, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        context['is_admin'] = self.request.user.is_staff
        context['primary_title'] = self.object.name

        return context

    def test_func(self):
        thread = self.get_object()
        if self.request.user.is_staff:
            return True
        else:
            user_groups = self.request.user.groups.all()
            return thread.groups.filter(id__in=user_groups).exists()


@method_decorator(group_required('user'), name='dispatch')
class ThreadDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Thread

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        archive_thread = self.get_object()
        delete_thread(request.user, archive_thread)
        return HttpResponseRedirect(reverse_lazy('forums'))

    def test_func(self):
        return self.request.user.is_staff


@method_decorator(group_required('user'), name='dispatch')
class PostCreateView(LoginRequiredMixin, CreateView):
    model = ForumPost
    form_class = ForumPostForm
    template_name = 'create_post.html'

    def dispatch(self, request, *args, **kwargs):
        thread = get_object_or_404(Thread, id=self.kwargs['thread_id'])
        can_create_post = False
        if request.user.is_staff:
            can_create_post = True
        else:
            user_groups = self.request.user.groups.all()
            can_create_post = thread.groups.filter(id__in=user_groups).exists()

        if can_create_post:
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("<h1>You don't have permission to create posts on this thread. </h1>")

    def post(self, request, thread_id):
        form = ForumPostForm(request.POST)
        if form.is_valid():
            form.instance.thread = get_object_or_404(
                Thread, id=thread_id)
            form.instance.user = self.request.user
            form.instance.row_action = 'CREATE'
            form.save()
            return HttpResponseRedirect(reverse_lazy('post', kwargs={'thread_id': thread_id,  'pk': form.instance.id}))
        else:
            thread = get_object_or_404(Thread, id=thread_id)
            context = {'form': form,  'thread': thread}
            return render(request, self.template_name, context)

    def get(self, request, *args, **kwargs):
        form = ForumPostForm()
        thread = get_object_or_404(
            Thread, id=self.kwargs['thread_id'])
        context = {'form': form,  'thread': thread}
        return render(request, self.template_name,  context)


@method_decorator(group_required('user'), name='dispatch')
class PostDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = ForumPost
    template_name = 'post.html'
    context_object_name = 'post'
    form_class = ForumPostForm

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forum_post = get_object_or_404(ForumPost, id=self.kwargs.get('pk'))
        form = ForumPostForm(instance=forum_post)
        for field in form.fields:
            form.fields[field].widget.attrs['disabled'] = True
        context['form'] = form

        comment_form = ForumCommentForm()
        comments = self.object.comments.all().order_by('-date')
        for comment in comments:
            if comment.row_action == 'CREATE':
                comment.is_create_missing = False
                comment.author = comment.user
            else:
                comment_creation_info = get_comment_create_info(comment)
                comment_author_id, comment.create_date, comment.is_create_missing = comment_creation_info
                if comment_author_id != 'NOT FOUND':
                    comment_author = User.objects.get(
                        id=comment_author_id)
                else:
                    comment_author = 'NOT FOUND'
                comment.author = comment_author

        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(comments, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        context['comment_form'] = comment_form
        context['is_admin'] = self.request.user.is_staff
        context['primary_title'] = self.object.title
        return context

    def post(self, request, *args, **kwargs):
        forum_post = self.get_object()
        comment_form = ForumCommentForm(request.POST)
        if comment_form.is_valid():
            comment_form.instance.post = forum_post
            comment_form.instance.user = request.user
            comment_form.instance.row_action = 'CREATE'
            comment_form.save()
            return HttpResponseRedirect(reverse_lazy('post', kwargs={'thread_id': forum_post.thread_id,  'pk': forum_post.id}))

    def test_func(self):
        forum_post = self.get_object()
        if self.request.user.is_staff:
            return True
        else:
            user_groups = self.request.user.groups.all()
            return forum_post.thread.groups.filter(id__in=user_groups).exists()


@method_decorator(group_required('user'), name='dispatch')
class PostEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ForumPost
    form_class = ForumPostForm
    template_name = 'edit_post.html'
    context_object_name = 'post'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('post', kwargs={'thread_id': self.object.thread.id,  'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forum_post = get_object_or_404(ForumPost, id=self.kwargs.get('pk'))
        form = ForumPostForm(instance=forum_post)
        context['form'] = form
        context['is_admin'] = self.request.user.is_staff
        context['primary_title'] = self.object.title
        context['thread_id'] = self.object.thread.id
        context['post_id'] = self.object.id
        return context

    def post(self, request, *args, **kwargs):
        post_id = self.kwargs.get('pk')
        post = get_object_or_404(
            ForumPost, id=post_id)
        post_form = ForumPostForm(request.POST, instance=post)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            post.user = request.user
            post.row_action = 'EDIT'
            post.date = timezone.now()
            post.save()
            return HttpResponseRedirect(reverse_lazy('post', kwargs={'thread_id': post.thread_id,  'pk': post.id}))

    def test_func(self):
        forum_post = self.get_object()
        post_creation_info = get_post_create_info(forum_post)
        post_author_id, forum_post.create_date, forum_post.is_create_missing = post_creation_info
        if post_author_id != 'NOT FOUND':
            post_author = User.objects.get(id=post_author_id).name
        else:
            post_author = 'NOT FOUND'
        return (self.request.user == post_author and post_author != 'NOT FOUND') or self.request.user.is_staff


@method_decorator(group_required('user'), name='dispatch')
class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ForumPost

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        archive_post = self.get_object()
        thread_id = archive_post.thread.id
        with transaction.atomic():
            delete_post(request.user, archive_post)
        return HttpResponseRedirect(reverse_lazy('thread', kwargs={'pk': thread_id}))

    def test_func(self):
        forum_post = self.get_object()
        if forum_post.row_action == 'CREATE':
            post_author = forum_post.user
        else:
            post_creation_info = get_post_create_info(forum_post)
            post_author_id, forum_post.create_date, forum_post.is_create_missing = post_creation_info
            if post_author_id != 'NOT FOUND':
                post_author = User.objects.get(id=post_author_id).name
            else:
                post_author = 'NOT FOUND'

        return (self.request.user == post_author and post_author != 'NOT FOUND') or self.request.user.is_staff


@method_decorator(group_required('user'), name='dispatch')
class CommentEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ForumComment
    form_class = ForumCommentForm
    template_name = 'edit_comment.html'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comment = get_object_or_404(
            ForumComment, id=self.kwargs.get('pk'))
        form = ForumCommentForm(instance=comment)
        context['form'] = form
        context['is_admin'] = self.request.user.is_staff
        context['thread_id'] = self.object.post.thread.id
        context['post_id'] = self.object.post.id
        context['comment_id'] = self.object.id
        return context

    def post(self, request, *args, **kwargs):
        comment_id = self.kwargs.get('pk')
        comment = get_object_or_404(
            ForumComment, id=comment_id)
        comment_form = ForumCommentForm(request.POST, instance=comment)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.user = request.user
            comment.row_action = 'EDIT'
            comment.date = timezone.now()
            comment.save()
            return HttpResponseRedirect(reverse_lazy('post', kwargs={'thread_id': comment.post.thread_id,  'pk': comment.post.id}))

    def test_func(self):
        comment = self.get_object()
        if comment.row_action == 'CREATE':
            comment_author = comment.user
        else:
            comment_creation_info = get_comment_create_info(comment)
            comment_author_id, comment.create_date, comment.is_create_missing = comment_creation_info
            if comment_author_id != 'NOT FOUND':
                comment_author = User.objects.get(id=comment_author_id).name
            else:
                comment_author = 'NOT FOUND'
        return (self.request.user == comment_author and comment_author != 'NOT FOUND') or self.request.user.is_staff


@method_decorator(group_required('user'), name='dispatch')
class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ForumComment

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        archive_comment = self.get_object()
        thread_id = archive_comment.post.thread.id
        post_id = archive_comment.post.id
        with transaction.atomic():
            delete_comment(request.user, archive_comment)
        return HttpResponseRedirect(reverse_lazy('post', kwargs={'thread_id': thread_id,  'pk': post_id}))

    def test_func(self):
        comment = self.get_object()
        if comment.row_action == 'CREATE':
            comment_author = comment.user
        else:
            comment_creation_info = get_comment_create_info(comment)
            comment_author_id, comment.create_date, comment.is_create_missing = comment_creation_info
            if comment_author_id != 'NOT FOUND':
                comment_author = User.objects.get(id=comment_author_id).name
            else:
                comment_author = 'NOT FOUND'
        return (self.request.user == comment_author and comment_author != 'NOT FOUND') or self.request.user.is_staff

##                   ##
#   UTILITY METHODS
##                   ##


# THREAD UTILITY METHODS #


# Since this method has multiple operations that must succeed or fail together,
# Putting a transaction at the top of this method itself,  rather than calling
# the method within a transaction,  as I do with other utility delete methods.
# (Because Thread is the "top level" model of Forums, and isn't being
# called in a deletion loop like posts and comments are)
def delete_thread(usr, archive_thread):
    with transaction.atomic():
        archive_thread.row_action = 'DELETE'
        archive_thread.user = usr
        archive_thread.date = timezone.now()

        # First,  try to delete all the posts
        # which will in turn invoke deletion of all their
        # comments
        # If any deletion fails down the chain,  the whole deletion
        # process should be canceled.
        posts = archive_thread.posts.all().order_by('-date')
        for post in posts:
            delete_post(usr, post)

        # specify this is an deleted record
        # both save and delete must execute or fail together,
        # this keeps track of the time of deletion and
        # the user who deleted the record
        archive_thread.save()
        archive_thread.delete()
        return "success"


# POST UTILITY METHODS #

# Since this method has multiple operations that must succeed or fail together,
# call this method inside of transaction.
# Not putting a transaction at the top of this method itself,  b/c
# this method may be called inside of a delete_thread method.
# I want failures to propagate up the chain and cancel the
# whole delete sequence - or else have all the "CASCADE" of
# deletes succeed together.
def delete_post(usr, archive_post):

    archive_post.row_action = 'DELETE'
    archive_post.user = usr
    archive_post.date = timezone.now()

    # First,  try to delete all the comments
    # If this method is called inside a transaction,
    # All comment deletions should rollback if one fails
    comments = archive_post.comments.all().order_by('-date')
    for comment in comments:
        delete_comment(usr, comment)

    # Uncomment to run test cases for post failures
    # if "Post Failure" in archive_post.title:
    #    raise TestTransactionError("Test Delete Post Failure.")

    # specify this is an deleted record
    # both save and delete must execute or fail together,
    # this keeps track of the time of deletion and
    # the user who deleted the record
    archive_post.save()
    archive_post.delete()
    return "success"


# Used to get original date/author of an edited post
def get_post_create_info(post):
    author = ''
    oldest_date = ''
    is_create_missing = False

    post_history = ForumPostHistory.objects.filter(
        post_id=post.id,  row_action="CREATE")

    # there should be only one value.
    # we will set a flag if there is no row with method 'CREATE'  in ForumPostHistory
    oldest_post_record = post_history.first()

    if oldest_post_record:
        author = oldest_post_record.user
        oldest_date = oldest_post_record.date
    else:
        # DBAs TAKE NOTE: If a DBA deletes some older Forum Post History Records
        # then the row with the ForumPost's initial creation date/original author could have
        # been deleted and unavailable now!
        is_create_missing = True
        author = 'NOT FOUND'
        oldest_date = 'DATE NOT FOUND'
    return (author, oldest_date, is_create_missing)


# COMMENT UTILITY METHODS #

# Since this method has two operations that must succeed or fail together,
# call this method inside of transaction.
# Not putting a transaction at the top of this method itself,  b/c
# this method may be called inside of a delete_post method.
# I want failures to propagate up the chain and cancel the
# whole delete sequence - or else have all the "CASCADE" of
# deletes succeed together.


def delete_comment(usr, archive_comment):

    archive_comment.row_action = 'DELETE'
    archive_comment.user = usr
    archive_comment.date = timezone.now()

    # specify this is an deleted record
    # both save and delete must execute or fail together,
    # this keeps track of the time of deletion and
    # the user who deleted the record
    archive_comment.save()
    archive_comment.delete()

    # Uncomment to test error in a transaction after both operations complete successfully
    # if Comment about widgets" in archive_comment.content:
    #   raise TestTransactionError("Test Delete Comment Failure.")
    return "success"


# Used to get original date/author of an edited comment
def get_comment_create_info(comment):
    author = ''
    oldest_date = ''
    is_create_missing = False

    comment_history = ForumCommentHistory.objects.filter(
        comment_id=comment.id,  row_action="CREATE")

    # there should be only one value.
    # we will set a flag if there is no row with method 'CREATE'  in ForumCommentHistory
    oldest_comment_record = comment_history.first()
    if oldest_comment_record:
        author = oldest_comment_record.user
        oldest_date = oldest_comment_record.date
    else:
        # DBAs TAKE NOTE: If a DBA deletes some older Forum Comment History Records
        # then the row with the ForumComment's initial creation date/original author could have
        # been deleted and unavailable now!
        is_create_missing = True
        author = 'NOT FOUND'
        oldest_date = 'DATE NOT FOUND'
    return (author, oldest_date, is_create_missing)


# Use to test failure case of delete transaction
class TestTransactionError(Exception):
    pass
