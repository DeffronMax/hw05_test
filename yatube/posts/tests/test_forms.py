import datetime
from http import HTTPStatus
import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from ..models import Group, Post

User = get_user_model()
MEDIA_ROOT_TEMP = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=MEDIA_ROOT_TEMP)
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
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.image_for_new_post = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.post = Post.objects.create(
            text=self.text,
            pub_date=datetime.datetime.today().strftime("%m-%d-%Y"),
            author=self.user,
            group=self.group,
            image=self.image_for_new_post,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

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

    def test_edit_post2(self):
        """ Проверка редактирования all in """
        posts_count = Post.objects.count()
        post_edit = self.post
        text_old = post_edit.text
        form_data = {'text': 'Текст отредактирован'}
        response = self.authorized_client.post(
            reverse('post_edit',
                    kwargs={'username': self.user,
                            'post_id': post_edit.pk}),
            data=form_data,
            follow=True,
        )
        post_new = Post.objects.first()
        text_new = post_new.text
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(text_new, form_data['text'])
        self.assertIsNot(text_old, text_new)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_form_create(self):
        posts_count = Post.objects.count()
        forms = {
            'text': PostCreateFormTests.text,
            'group': self.group.id,
            'image': self.image_for_new_post.name,
        }
        self.authorized_client.post(reverse('new_post'),
                                    data=forms,
                                    follow=True)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text='test text')
                        .exists())
