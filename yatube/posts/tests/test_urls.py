from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username="Author")
        cls.not_author = User.objects.create_user(username="NotAuthor")
        cls.group = Group.objects.create(title="Group", slug='slug')
        cls.text = "test text"
        cls.post = Post.objects.create(text=cls.text, author=cls.author)
        cls.templates_url_names = {
            'misc/base.html': '/',
            'posts/group.html': f'/group/{cls.group.slug}/',
            'posts/new_post.html': '/new/',
            'posts/profile.html': f'/{cls.author.username}/',
            'posts/post.html': f'/{cls.author.username}/{cls.post.id}/'
        }
        cls.group_name = Group.objects.create(
            title="test_group"
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)

    def test_anon_user(self):
        """Гость ошибка редактирования"""
        for template, adress in self.templates_url_names.items():
            with self.subTest(adress=adress):
                if adress == reverse('new_post'):
                    response = self.guest_client.get(adress)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)
                else:
                    response = self.guest_client.get(adress)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.guest_client.get(f'/{self.author.username}/'
                                         f'{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_author_user(self):
        """автор редактирование"""
        for template, adress in self.templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_client.get(f'/{self.author.username}/'
                                              f'{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_author_user(self):
        """Не автор редактирование"""
        for template, adress in self.templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.not_author_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.not_author_client.get(f'/{self.author.username}/'
                                              f'{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_wrong_uri_returns_404(self):
        response = self.client.get('test/404/code/')
        self.assertEqual(response.status_code, 404)
