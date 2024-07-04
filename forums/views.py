from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
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
        return context


class ThreadCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Thread
    form_class = ThreadForm
    template_name = 'create_thread.html'
    success_url = reverse_lazy('forums')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        response = super().form_valid(form)
        role_id = self.request.POST.get('ThreadRole')
        role = get_object_or_404(ThreadRole, id=role_id)
        ThreadRole.objects.create(thread=self.object, group=role.group)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ThreadRoles'] = ThreadRole.objects.all()
        return context


class ThreadDetailView(LoginRequiredMixin, DetailView):
    model = Thread
    template_name = 'thread.html'
    context_object_name = 'thread'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['posts'] = self.object.posts.all()
        context['is_admin'] = self.request.user.is_staff
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = ForumPost
    form_class = ForumPostForm
    template_name = 'create_post.html'

    def form_valid(self, form):
        form.instance.thread = get_object_or_404(
            Thread, id=self.kwargs['thread_id'])
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('thread', kwargs={'pk': self.kwargs['thread_id']})


class PostDetailView(LoginRequiredMixin, DetailView):
    model = ForumPost
    template_name = 'post.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.all()
        context['form'] = ForumCommentForm()
        context['is_admin'] = self.request.user.is_staff
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ForumCommentForm(request.POST)
        if form.is_valid():
            form.instance.post = self.object
            form.instance.author = request.user
            form.save()
            return redirect('post', thread_id=self.object.thread.id, pk=self.object.id)
        return self.render_to_response(self.get_context_data(form=form))


class PostEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ForumPost
    form_class = ForumPostForm
    template_name = 'edit_post.html'

    def get_success_url(self):
        return reverse_lazy('thread', kwargs={'pk': self.object.thread.id})

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
