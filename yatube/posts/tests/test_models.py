from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Post, Group

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.long_post = Post.objects.create(
            text="Тестовый текст длиной более 15 символов для правильной"
                 " проверки тестом",
            author=User.objects.create_user(username="test_user1")
        )
        cls.short_post = Post.objects.create(
            text="Текст",
            author=User.objects.create_user(username="test_user2")
        )

    def test_long_post_name_is_title_field(self):
        expected_object_name = PostModelTest.long_post.text[:15]
        self.assertEqual(expected_object_name, str(PostModelTest.long_post))

    def test_short_post_name_is_title_field(self):
        expected_object_name = PostModelTest.short_post.text
        self.assertEqual(expected_object_name, str(PostModelTest.short_post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_name = Group.objects.create(
            title="название группы"
        )

    def test_group_name_is_title_field(self):
        expected_object_name = GroupModelTest.group_name.title
        self.assertEqual(expected_object_name, str(GroupModelTest.group_name))
