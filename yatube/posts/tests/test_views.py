import datetime
import http
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms

from ..models import Post, Group

User = get_user_model()


class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='test title',
            slug='test_slug',
            description='test_description'
        )
        cls.post = Post.objects.create(
            text='Тест пятнадцати символов',
            author=cls.user,
            group=cls.group
        )

        cls.templates_url_names = {
            'misc/index.html': reverse('index'),
            'posts/group.html': reverse('group', kwargs={
                'slug': cls.group.slug}),
            'posts/new_post.html': reverse('new_post'),
        }
        # cls.templates_url_names = {
        #     'misc/index.html': {
        #         'url': reverse('index'),
        #         'context': ('page',)
        #     },
        #     'posts/group.html': {
        #         'url': reverse('group', kwargs={
        #         'slug': cls.group.slug
        #         }),
        #         'context': ('page', 'group', 'posts')
        #     }
        # }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        first_object = response.context['page'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, self.post.text)

    def test_group_shows_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': self.group.slug})
        )
        # Нужно ли в идеале еще добавить year, page ? Мнения разделились.
        self.assertEqual(response.context['group'], self.group)
        self.assertEqual(response.context['page'][0], self.post)

    # UPD DEADLINE ааа, позже будур азбираться ))
    # Привет ревьювер, тут хотелось сделать проверку всех context.
    # def test_all_context(self):
    #     for template in self.templates_url_names:
    #         response = self.authorized_client.get(
    #             self.templates_url_names[template]['url']
    #         )
    #         for context in self.templates_url_names[template]['context']:
    #             self.assertIn(context, response.context)

    def test_new_post_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField
        }
        for value, field_type in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, field_type)

    def test_post_correct_group(self):
        """Шаблон correct group сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        post = response.context['page'][0]
        group = post.group
        self.assertEqual(group, self.group)

    def test_edit_post_shows_correct_context(self):
        """Шаблон edit_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('post_edit', kwargs={
            'username': self.user.username,
            'post_id': self.post.id
        }))

        form_fields = {
            'text': forms.fields.CharField,
        }
        for value, exeption in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, exeption)

    def test_context_profile(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('profile', kwargs={
            'username': self.user.username,
        }))

        profile = {
            'author': self.post.author,
        }
        for value, exp in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, exp)
        test_page = response.context['page'][0]
        self.assertEqual(test_page, self.user.posts.all()[0])

    def test_post_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('post', kwargs={
            'username': self.user.username,
            'post_id': self.post.id
        }))
        profile = {
            'author': self.post.author,
            'post': self.post
        }
        for value, exeption in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, exeption)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.authorized_user = Client()
        cls.authorized_user.force_login(cls.user)
        cls.group = Group.objects.create(title='TestGroup',
                                         slug='test_slug',
                                         description='Test description')
        for i in range(13):
            cls.post = Post.objects.create(
                author=cls.user, text='Тестовый пост {i}',
                group=cls.group)
        cls.templates_pages_names = {
            'misc/index.html': reverse('index'),
            'posts/group.html': reverse(
                'group',
                kwargs={'slug': cls.group.slug}
            ),
            'posts/profile.html': reverse('profile', kwargs={
                'username': cls.user.username})}

    def test_first_page_contains_ten_records(self):
        """Проверка паджинатора 10 постов на 1 странице"""
        for adress, reverse_name in self.templates_pages_names.items():
            with self.subTest(adress=adress):
                response = self.client.get(reverse_name)
                self.assertEqual(len(
                    response.context.get('page').object_list), 10
                )

    def test_second_page_contains_three_records(self):
        """Проверка паджинатора 3 поста на 2 странице"""
        for adress, reverse_name in self.templates_pages_names.items():
            with self.subTest(adress=adress):
                response = self.client.get(reverse_name + '?page=2')
                self.assertEqual(len(
                    response.context.get('page')), 3
                )


class PostImageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cache.clear()
        cls.user = User.objects.create_user(username='leo')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Cats',
            slug='group_cats',
            description='Тестовое описание группы любителей котиков'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Это тестовый текст поста, текст поста, поста, поста.',
            group=cls.group,
            author=cls.user,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_index_page_shows_correct_context(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context.get('page').object_list[0].image,
                         self.post.image)

    def test_profile_page_shows_correct_context(self):
        response = self.client.get(reverse('profile', kwargs={
            'username': self.user.username,
        }))
        self.assertEqual(response.context.get('page').object_list[0].image,
                         self.post.image)

    def test_group_page_shows_correct_context(self):
        response = self.client.get(
            reverse('group', kwargs={'slug': self.group.slug}))
        self.assertEqual(response.context.get('page').object_list[0].image,
                         self.post.image)

    def test_post_view_page_shows_correct_context(self):
        response = self.client.get(reverse('post', kwargs={
            'username': self.user.username,
            'post_id': self.post.id
        }))
        self.assertEqual(response.context.get('post').image,
                         self.post.image)
        print()

    def test_post_view_page_shows_correct_context(self):
        response = self.client.get(reverse('post', kwargs={
            'username': self.user.username,
            'post_id': self.post.id
        }))
        self.assertEqual(response.context.get('post').image,
                         self.post.image)
