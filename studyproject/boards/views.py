import http

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import ListView, UpdateView

from studyproject.boards.forms import NewTopicForm, PostForm
from studyproject.boards.models import Board, Post, Topic

# def home(request):
#    boards = Board.objects.all()
#    context = {'boards': boards}
#
#    return render(request, template_name='home.html', context=context)


class BoardListView(ListView):
    model = Board
    context_object_name = 'boards'
    template_name = 'home.html'

# def board_topics(request, pk):
#    board = get_object_or_404(Board, pk=pk)
#    queryset = board.topics.order_by('-last_updated').annotate(replies=Count('posts')-1)
#
#    page = request.GET.get('page', 1) # pegando o parâmetro página. retorna 1 se não tiver
#    paginator = Paginator(queryset, 10) # definindo a paginação
#
#    try:
#        topics = paginator.page(page) # pegando a paginação definida
#    except PageNotAnInteger:
#        topics = paginator.page(1)
#    except EmptyPage:
#        topics = paginator.page(paginator.num_pages)
#
#    return render(request, template_name='topics.html', context={'board': board, 'topics': topics})


class TopicListView(ListView):
    """
    Using GCBV and pagination will make available the fallowing variables in the template(topics.html)
    paginator, page_obj, is_paginated, object_list
    """
    model = Topic
    context_object_name = 'topics'
    template_name = 'topics.html'
    paginate_by = 10

    # adicionando o objeto board no context para poder ser usado em topics.html
    # chamado após o queryset
    def get_context_data(self, **kwargs):
        kwargs['board'] = self.board
        return super().get_context_data(**kwargs)

    # o self.kwargs é como se fosse o atributo params de todos os controller do grails
    def get_queryset(self):
        """"""
        self.board = get_object_or_404(Board, pk=self.kwargs.get('pk'))
        queryset = self.board.topics.order_by(
            '-last_updated').annotate(replies=Count('posts') - 1)
        return queryset


@login_required
def new_topic(request, pk):
    board = get_object_or_404(Board, pk=pk)

    print(f'Board: {board}')
    print(f'User: {request.user}')

    if request.method == 'POST':
        form = NewTopicForm(request.POST)

        if form.is_valid():
            topic = form.save(commit=False)
            topic.board = board
            topic.starter = request.user
            topic.save()
            post = Post.objects.create(
                message=form.cleaned_data.get('message'),
                topic=topic,
                created_by=user
            )

            return redirect('topic_posts', pk=pk, topic_pk=topic.pk)
    else:
        form = NewTopicForm()

    return render(request, template_name='new_topic.html', context={'board': board, 'form': form})


def topic_posts(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    topic.views += 1
    topic.save()
    return render(request, 'topic_posts.html', {'topic': topic})


class PostListView(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'topic_posts.html'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        session_key = 'viewed_topic_{}'.format(self.topic.pk)
        if not self.request.session.get(session_key, False):
            self.topic.views += 1
            self.topic.save()
            self.request.session[session_key] = True

        kwargs['topic'] = self.topic
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.topic = get_object_or_404(Topic, board__pk=self.kwargs.get(
            'pk'), pk=self.kwargs.get('topic_pk'))
        # ordenar é fundamental para que o paginate funcione
        queryset = self.topic.posts.order_by('created_at')
        return queryset


@login_required
def reply_topic(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    user = User.objects.first()

    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic = topic
            post.created_by = request.user
            post.save()

            topic.last_updated = timezone.now()
            topic.save()

            return redirect('topic_posts', pk=pk, topic_pk=topic_pk)
    else:
        form = PostForm()

    return render(request, template_name='reply_topic.html', context={'topic': topic, 'form': form})


@method_decorator(login_required, name='dispatch')
class PostUpdateView(UpdateView):
    model = Post
    fields = ('message',)
    template_name = 'edit_post.html'
    pk_url_kwarg = 'post_pk'
    context_object_name = 'post'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.user)

    def form_valid(self, form):
        post = form.save(commit=False)
        post.updated_by = self.request.user
        post.updated_at = timezone.now()
        post.save()

        return redirect('topic_posts', pk=post.topic.board.pk, topic_pk=post.topic.pk)
