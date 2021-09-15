from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']


class CommentForm(forms.ModelForm):
    """Форма комментариев"""

    class Meta:
        model = Comment
        fields = ['text']
        help_texts = {
            'text': 'Ваш комментарий',
        }
        labels = {'text': 'Текст комментария'}
