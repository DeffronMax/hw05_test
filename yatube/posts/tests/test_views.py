import http
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse
from django import forms

from ..models import Post, Group, Follow

User = get_user_model()


class ViewsTests(TestCase):
    """Привет ревьювер, я знаю что моя работа далека от совершенства,
    но прошу не судить строго. После обновления пришлось
    перелопатить уже готовую на тот момент к сдаче работу,
    и дедлайн горит, академов нет :( """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
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
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse('posts:group_posts', kwargs={
                'slug': cls.group.slug}),
            'posts/create_post.html': reverse('posts:post_create'),
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0, self.post.text)

    def test_group_shows_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_new_post_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
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
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        group = post.group
        self.assertEqual(group, self.group)

    def test_edit_post_shows_correct_context(self):
        """Шаблон edit_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={
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
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username,
                            }))

        profile = {
            'author': self.post.author,
        }
        for value, exp in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, exp)
        test_page = response.context['page_obj'][0]
        self.assertEqual(test_page, self.user.posts.all()[0])

    def test_post_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.id
            }))
        profile = {
            'post': self.post
        }
        for value, exeption in profile.items():
            with self.subTest(value=value):
                context = response.context[value]
                self.assertEqual(context, exeption)

    def test_cache_index_page(self):
        post3 = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group,
        )
        response = self.guest_client.get(reverse('posts:index'))
        posts_counter = response.context.get('page_obj').paginator.count
        self.assertEqual(posts_counter, Post.objects.count())
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, 'Тестовый пост')
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author.username, self.user.username)
        page_bytes = response.content
        Post.objects.get(pk=post3.id).delete()
        response1 = self.guest_client.get(reverse('posts:index'))
        page_bytes2 = response1.content
        self.assertEqual(page_bytes, page_bytes2)
        cache.clear()
        response2 = self.guest_client.get(reverse('posts:index'))
        page_bytes2 = response2.content
        self.assertNotEqual(page_bytes, page_bytes2)

    def test_new_post_follower(self):
        """ Новая запись пользователя появляется в ленте подписчиков """
        self.user = User.objects.create_user(username='mr.Test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': ViewsTests.post.author}))
        response = self.authorized_client.get(reverse('posts:follow_index'))
        post_response = response.context['page_obj'][0]
        self.assertEqual(self.post.text, post_response.text)
        self.assertEqual(self.post.author, post_response.author)
        self.assertEqual(self.post.group, post_response.group)

    def test_new_post_not_follower(self):
        """Новая запись пользователя не появляется в ленте неподписчиков"""
        Post.objects.create(author=self.user,
                            text='test follow text',
                            group=self.group)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(response.context.get('page_obj').paginator.count, 0)


class TestFollow(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestAuthor')
        cls.group = Group.objects.create(title='TestGroup',
                                         slug='test_slug',
                                         description='Test description')
        cls.follow_user = User.objects.create_user(username='TestUser')

    def setUp(self):
        self.authorized_user = Client()
        self.authorized_user.force_login(self.follow_user)

    def test_auth_user_unfollow(self):
        follow_count1 = Follow.objects.count()
        follow = Follow.objects.filter(author=self.user,
                                       user=self.follow_user)
        self.assertEqual(follow.first(), None)
        response = self.authorized_user.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username})
        )
        follow_count2 = Follow.objects.count()
        self.assertEqual(follow_count2, follow_count1 + 1)
        follow = Follow.objects.first()
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(follow.author, self.user)
        self.assertEqual(follow.user, self.follow_user)
        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)

    def test_view_unfollow(self):
        following_count = Follow.objects.all().count()
        self.assertEqual(Follow.objects.count(), following_count)
        follow = Follow.objects.filter(
            author=self.user,
            user=self.follow_user
        )
        self.assertEqual(follow.first(), None)

    def test_page_unfollow(self):
        response = self.authorized_user.get(
            reverse('posts:follow_index')
        )
        context = response.context['page_obj']
        self.assertEqual(context.paginator.count, 0)


class TestComments(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.comment_user = User.objects.create_user(username='TestCommentUser')
        cls.post = Post.objects.create(text='Test text', author=cls.user)
        cls.url_comment = reverse('posts:add_comment',
                                  kwargs={'post_id': cls.post.id})

    def setUp(self):
        self.anonymous = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.comment_user)

    def test_comment_anonymous(self):
        response = self.anonymous.get(self.url_comment)
        urls = '/auth/login/?next={}'.format(self.url_comment)
        self.assertRedirects(response, urls, status_code=http.HTTPStatus.FOUND)

    def test_comment_auth(self):
        response = self.authorized_user.post(self.url_comment, {
            'text': 'test comment'
        }, follow=True)
        self.assertContains(response, 'test comment')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='noauthor')
        cls.group = Group.objects.create(
            title='Тестовая',
            slug='test-slug')
        for i in range(13):
            cls.post = Post.objects.create(
                text='Привет, как дела?',
                author=PaginatorViewsTest.author,
                group=PaginatorViewsTest.group
            )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.author)

    def test_index_paginator_first_page(self):
        """Проверка паджинатора 10 постов на 1 странице"""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_paginator_next_page(self):
        """Проверка паджинатора 3 поста на 2 странице"""
        response = (self.guest_client.get(reverse('posts:index')
                                          + '?page=2'))
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_list_paginator_first_page(self):
        slug_test = PaginatorViewsTest.group.slug
        response = self.guest_client.get(reverse('posts:group_posts',
                                                 kwargs={'slug': slug_test}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_list_next_page(self):
        slug_test = PaginatorViewsTest.group.slug
        response = (self.guest_client.
                    get(reverse('posts:group_posts',
                                kwargs={'slug': slug_test}) + '?page=2'))
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_profile_paginator_first_page(self):
        slug_author = PaginatorViewsTest.post.author
        response = (self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': slug_author})))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_paginator_next_page(self):
        slug_author = PaginatorViewsTest.post.author
        response = (self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': slug_author}) + '?page=2'))
        self.assertEqual(len(response.context['page_obj']), 3)


class PostImageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cache.clear()
        cls.user = User.objects.create_user(username='test_bob')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Cats',
            slug='group_cats',
            description='Тестовое описание'
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
            text='Тест текст22',
            group=cls.group,
            author=cls.user,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_index_page_shows_correct_context(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(response.context.get('page_obj').object_list[0].image,
                         self.post.image)

    def test_profile_page_shows_correct_context(self):
        response = self.client.get(reverse('posts:profile', kwargs={
            'username': self.user.username,
        }))
        self.assertEqual(response.context.get('page_obj').object_list[0].image,
                         self.post.image)

    def test_group_page_shows_correct_context(self):
        response = self.client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}))
        self.assertEqual(response.context.get('page_obj').object_list[0].image,
                         self.post.image)

    def test_post_view_page_shows_correct_context(self):
        response = self.client.get(reverse('posts:post_detail', kwargs={
            'post_id': self.post.id
        }))
        self.assertEqual(response.context.get('post').image,
                         self.post.image)
