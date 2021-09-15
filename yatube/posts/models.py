from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200, unique=True, verbose_name='Имя группы'
    )
    slug = models.SlugField(
        max_length=150, unique=True, verbose_name='Адрес группы'
    )
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name_plural = 'Группы'
        verbose_name = 'Группа'

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        verbose_name='Дата создания поста', auto_now_add=True
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL,
        related_name='posts', blank=True, null=True,
        verbose_name='Группа'
    )
    image = models.ImageField(
        upload_to='posts/', blank=True,
        null=True, verbose_name='Картинка'
    )

    class Meta:
        verbose_name_plural = 'Посты'
        verbose_name = 'Пост'
        ordering = ['-pub_date']

    def __str__(self) -> str:
        text = self.text
        if len(text) > 15:
            text = text[:15]
        return text


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments',
                             verbose_name='Пост')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments',
                               verbose_name='Автор')
    text = models.TextField(verbose_name='Текст комментария')
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Дата комментария')

    class Meta:
        ordering = ['-created']
        verbose_name_plural = 'Комментарии'

    def __str__(self) -> str:
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='Подписчик')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following',
                               verbose_name='Автор поста')

    class Meta:
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(fields=("user", "author"),
                                    name="unique_list"),
            models.CheckConstraint(check=~models.Q(user=models.F("author")),
                                   name="author")
        )

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
