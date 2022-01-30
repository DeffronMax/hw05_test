from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Post(models.Model):
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        verbose_name='Группа',
        blank=True, null=True,
        related_name='posts'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self) -> str:
        text = self.text
        if len(text) > 15:
            text = text[:15]
        return text


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    slug = models.SlugField(unique=True, verbose_name='Короткая ссылка группы')
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name='Пост',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(verbose_name='Текст')
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Дата публикации')

    class Meta:
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь подписчик',
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        verbose_name='Пользователь автор',
        on_delete=models.CASCADE,
        related_name='following'
    )

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
