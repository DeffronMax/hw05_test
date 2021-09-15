from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
        'group': group,
        'posts': posts,
    }
    return render(request,
                  'posts/group.html',
                  context
                  )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = user.is_authenticated and (Follow
                                           .objects
                                           .filter(user=user,
                                                   author=author)
                                           .exists())
    context = {
        'author': author,
        'following': following,
        'page': page,
        'paginator': paginator,
    }
    return render(request, 'posts/profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(
        Post.objects.filter(author__username=username),
        id=post_id
    )
    form = CommentForm(request.POST or None)
    comments = post.comments.select_related('author').all()
    return render(
        request,
        'posts/post.html',
        {'author': post.author, 'post': post,
         'comments': comments, 'form': form}
    )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if username != request.user.username:
        return redirect('post', username=username, post_id=post.id)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post.id)

    context = {
        'form': form
    }
    return render(request, 'posts/new_post.html', context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        context = {
            'form': form,
        }
        return render(request, 'posts/new_post.html', context)

    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('index')


@login_required()
def add_comment(request, username, post_id):
    post_item = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post_item
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'posts/comments.html', {'form': form,
                                                   'post': post_item})


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'posts/follow.html',
        {'page': page,
         'post_list': post_list}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(author=author, user=request.user)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(author=author, user=request.user).delete()
    return redirect('profile', username=username)
