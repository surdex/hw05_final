from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class ModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='тест' * 20,
            author=User.objects.create_user(username='test_user'),
        )
        cls.group = Group.objects.create(
            title='test group',
            slug='test-group',
        )

    def test_str_method(self):
        post = ModelTest.post
        group = ModelTest.group
        expected_objects = [(post.text[:15], str(post)),
                            (group.title, str(group))]

        for expected in expected_objects:
            with self.subTest(expected=expected[0]):
                self.assertEqual(expected[0], expected[1])

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        model_post = ModelTest.post
        field_verboses = {
            'text': 'Текст публикации',
            'group': 'Группа',
        }

        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    model_post._meta.get_field(value).verbose_name,
                    expected,
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        model_post = ModelTest.post
        field_help_text = {
            'text': 'Здесь Вы можете рассказать, что у Вас нового.',
            'group': 'Выберите группу, которая лучше всего '
                     'подходит к теме Вашего поста.',
        }

        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    model_post._meta.get_field(value).help_text, expected
                )
