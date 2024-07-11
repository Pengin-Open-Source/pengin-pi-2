from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from forums.models import Thread, ForumPost, ForumComment, ThreadRole
from forums.forms import ThreadForm, ForumPostForm, ForumCommentForm


class ForumsListView(LoginRequiredMixin, ListView):

    queryset = Thread.objects.all()
    template_name = 'threads.html'
    model = Thread

    context_object_name = 'threads'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self.request.user.is_staff
        context['primary_title'] = 'Forums'
        threads = self.queryset.order_by('name')
        # Similar to what Sincere is using for companies
        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(threads, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj

        return context


class ThreadCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Thread
    form_class = ThreadForm
    template_name = 'create_thread.html'
    success_url = reverse_lazy('forums')

    def test_func(self):
        return self.request.user.is_staff

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        query_groups = request.user.groups.all()
        roles = list(query_groups.values('id', 'name'))
        form = ThreadForm()
        context = {'roles': roles, 'form': form}
        return render(request, self.template_name,  context)

    @method_decorator(login_required)
    def post(self, request):
        form = ThreadForm(request.POST)
        if form.is_valid():
            role = self.request.POST.get('role')
            thread = form.save()
            selected_role = request.user.groups.get(pk=role)
            ThreadRole.objects.create(thread=thread, group=selected_role)
            return HttpResponseRedirect(reverse_lazy('thread', kwargs={'pk': form.instance.pk}))


class ThreadDetailView(LoginRequiredMixin, DetailView):
    model = Thread
    template_name = 'thread.html'
    context_object_name = 'thread'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = self.object.posts.all().order_by('-date')
        page_number = self.request.POST.get(
            'page-number', 1) if self.request.method == "POST" else self.request.GET.get('page', 1)
        paginator = Paginator(posts, 10)
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        context['is_admin'] = self.request.user.is_staff
        context['primary_title'] = self.object.name
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = ForumPost
    form_class = ForumPostForm
    template_name = 'create_post.html'

    @method_decorator(login_required)
    def post(self, request, thread_id):
        form = ForumPostForm(request.POST)
        if form.is_valid():
            form.instance.thread = get_object_or_404(
                Thread, id=thread_id)
            form.instance.author = self.request.user
            form.save()
            return HttpResponseRedirect(reverse_lazy('post', kwargs={'thread_id': thread_id,  'pk': form.instance.id}))
        else:
            thread = get_object_or_404(Thread, id=thread_id)
            context = {'form': form,  'thread': thread}
            return render(request, self.template_name, context)

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        form = ForumPostForm()
        thread = get_object_or_404(
            Thread, id=self.kwargs['thread_id'])
        context = {'form': form,  'thread': thread}
        return render(request, self.template_name,  context)


class PostDetailView(LoginRequiredMixin, DetailView):
    model = ForumPost
    template_name = 'post.html'
    context_object_name = 'post'
    form_class = ForumPostForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forum_post = get_object_or_404(ForumPost, id=self.kwargs.get('pk'))
        form = ForumPostForm(instance=forum_post)
        for field in form.fields:
            form.fields[field].widget.attrs['disabled'] = True
        context['form'] = form
        comment_form = ForumCommentForm()
        comments = self.object.comments.all().order_by('-date')
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
        self.object = self.get_object()
        comment_form = ForumCommentForm(request.POST)
        if comment_form.is_valid():
            comment_form.instance.post = self.object
            comment_form.instance.author = request.user
            comment_form.save()
            return HttpResponseRedirect(reverse_lazy('post', kwargs={'thread_id': self.object.thread_id,  'pk': self.object.id}))
        # return self.render_to_response(self.get_context_data(form=form))


class PostEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ForumPost
    form_class = ForumPostForm
    template_name = 'edit_post.html'
    context_object_name = 'post'

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

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff


class ThreadDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Thread
    template_name = 'delete_thread.html'
    success_url = reverse_lazy('forums')

    def test_func(self):
        return self.request.user.is_staff


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ForumPost
    template_name = 'delete_post.html'

    def get_success_url(self):
        return reverse_lazy('thread', kwargs={'pk': self.object.thread.id})

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author or self.request.user.is_staff


class CommentEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ForumComment
    form_class = ForumCommentForm
    template_name = 'edit_comment.html'

    def get_success_url(self):
        return reverse_lazy('post', kwargs={'thread_id': self.object.post.thread.id, 'pk': self.object.post.id})

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author or self.request.user.is_staff


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ForumComment
    template_name = 'delete_comment.html'

    def get_success_url(self):
        return reverse_lazy('post', kwargs={'thread_id': self.object.post.thread.id, 'pk': self.object.post.id})

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author or self.request.user.is_staff
