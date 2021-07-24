from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(title='test_group', slug='test_slug')
        cls.text = "test text"

    def setUp(self) -> None:
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_new_post_added(self):
        """ проверка создания нового поста """
        posts_count = Post.objects.count()
        form_data = {'text': PostCreateFormTests.text,
                     'group': self.group.id}
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        last_post = Post.objects.last()
        check_list = {
            response.status_code: HTTPStatus.OK,
            posts_count + 1: Post.objects.count(),
            last_post.text: form_data['text'],
            last_post.group.id: self.group.id,
            last_post.author: self.user
        }
        for value, expected in check_list.items():
            with self.subTest(expected):
                self.assertEqual(value, expected)

    def _get_urls(self, username, post_id):
        return {
            'index': reverse(viewname='index'),
            'profile': reverse(
                viewname='profile',
                kwargs={'username': username},
            ),
            'post': reverse(
                viewname='post',
                kwargs={
                    'username': username,
                    'post_id': post_id,
                },
            ),
            'post_edit': reverse(
                viewname='post_edit',
                kwargs={
                    'username': username,
                    'post_id': post_id,
                },
            ),
        }

    def test_edit_post(self):
        # создаем пост в testcase
        old_post = Post.objects.create(
            text=PostCreateFormTests.text,
            author=PostCreateFormTests.user,
            group=PostCreateFormTests.group,
        )
        urls = self._get_urls(
            PostCreateFormTests.user.username,
            old_post.id,
        )

        new_post_text = 'Обновленный текст'
        self.authorized_client.post(
            path=urls['post_edit'],
            data={'text': new_post_text},
        )
        last_post = Post.objects.last()
        # Проверка, что в БД поменялся текст
        self.assertNotEqual(PostCreateFormTests.text, last_post.text)
        # Проверки, что на всех страницах есть новый текст
        for url in urls.values():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertContains(response, new_post_text, status_code=200)
