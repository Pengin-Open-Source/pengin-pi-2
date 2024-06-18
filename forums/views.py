# forums/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Thread, ForumPost, ForumComment, Role
from .forms import ThreadForm, ForumPostForm, ForumCommentForm

@login_required
def forums(request):
    threads = Thread.objects.all()
    return render(request, 'forums/threads.html', {'threads': threads, 'is_admin': request.user.is_staff})

@login_required
def create_thread(request):
    if not request.user.is_staff:
        return redirect('forums')
    
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save()
            # Assuming role is provided in POST data
            role_id = request.POST.get('role')
            role = get_object_or_404(Role, id=role_id)
            Role.objects.create(thread=thread, role=role)
            return redirect('forums')
    else:
        form = ThreadForm()
    roles = Role.objects.all()
    return render(request, 'forums/create_thread.html', {'form': form, 'roles': roles})

@login_required
def thread(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
    posts = thread.posts.all()
    return render(request, 'forums/thread.html', {'thread': thread, 'posts': posts, 'is_admin': request.user.is_staff})

@login_required
def create_post(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
    if request.method == 'POST':
        form = ForumPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.thread = thread
            post.author = request.user
            post.save()
            return redirect('thread', thread_id=thread.id)
    else:
        form = ForumPostForm()
    return render(request, 'forums/create_post.html', {'form': form, 'thread': thread})

@login_required
def post(request, thread_id, post_id):
    post = get_object_or_404(ForumPost, id=post_id, thread__id=thread_id)
    comments = post.comments.all()
    if request.method == 'POST':
        form = ForumCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('post', thread_id=thread_id, post_id=post_id)
    else:
        form = ForumCommentForm()
    return render(request, 'forums/post.html', {'post': post, 'comments': comments, 'form': form})

@login_required
def delete_thread(request, id):
    if not request.user.is_staff:
        return redirect('forums')
    thread = get_object_or_404(Thread, id=id)
    thread.delete()
    return redirect('forums')

@login_required
def delete_post(request, id):
    post = get_object_or_404(ForumPost, id=id)
    thread_id = post.thread.id
    if request.user == post.author or request.user.is_staff:
        post.delete()
        return redirect('thread', thread_id=thread_id)
    return redirect('forums')

@login_required
def delete_comment(request, id):
    comment = get_object_or_404(ForumComment, id=id)
    post_id = comment.post.id
    thread_id = comment.post.thread.id
    if request.user == comment.author or request.user.is_staff:
        comment.delete()
        return redirect('post', thread_id=thread_id, post_id=post_id)
    return redirect('forums')

@login_required
def edit_post(request, thread_id, post_id):
    post = get_object_or_404(ForumPost, id=post_id, thread__id=thread_id)
    if request.method == 'POST':
        form = ForumPostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('thread', thread_id=thread_id)
    else:
        form = ForumPostForm(instance=post)
    return render(request, 'forums/edit_post.html', {'form': form, 'thread_id': thread_id, 'post_id': post_id})

@login_required
def edit_comment(request, thread_id, post_id, comment_id):
    comment = get_object_or_404(ForumComment, id=comment_id, post__id=post_id, post__thread__id=thread_id)
    if request.method == 'POST':
        form = ForumCommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('post', thread_id=thread_id, post_id=post_id)
    else:
        form = ForumCommentForm(instance=comment)
    return render(request, 'forums/edit_comment.html', {'form': form, 'thread_id': thread_id, 'post_id': post_id, 'comment_id': comment_id})
