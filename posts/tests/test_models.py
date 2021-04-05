from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Comment, Group, Post

User = get_user_model()


class ModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.post = Post.objects.create(
            text='тест' * 20,
            author=cls.user
        )
        cls.group = Group.objects.create(
            title='test group',
            slug='test-group'
        )
        cls.comment = Comment.objects.create(
            text='Test comment',
            author=cls.user,
            post=cls.post
        )

    def test_str_method(self):
        post = ModelTest.post
        group = ModelTest.group
        comment = ModelTest.comment
        expected_objects = {
            str(post): post.text[:15],
            str(group): group.title,
            str(comment): comment.text
        }

        for values, expected in expected_objects.items():
            with self.subTest(values=values):
                self.assertEqual(values, expected)

    def test_post_verbose_names(self):
        """verbose_name в полях Post совпадает с ожидаемым."""
        model_post = ModelTest.post
        field_verboses = {
            'text': 'Текст публикации',
            'group': 'Группа',
            'image': 'Изображение',
        }

        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    model_post._meta.get_field(value).verbose_name,
                    expected,
                )

    def test_post_help_texts(self):
        """help_text в полях Post совпадает с ожидаемым."""
        model_post = ModelTest.post
        field_help_text = {
            'text': 'Здесь Вы можете рассказать, что у Вас нового.',
            'group': 'Выберите группу, которая лучше всего '
                     'подходит к теме Вашего поста.',
            'image': 'Загрузите картинку',
        }

        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    model_post._meta.get_field(value).help_text, expected
                )

    def test_comment_verbose_names(self):
        """verbose_name в полях Comment совпадает с ожидаемым."""
        model_comment = ModelTest.comment

        self.assertEqual(
            model_comment._meta.get_field('text').verbose_name,
            'Текст комментария'
        )

    def test_comment_help_texts(self):
        """help_text в полях Comment совпадает с ожидаемым."""
        model_comment = ModelTest.comment

        self.assertEqual(
            model_comment._meta.get_field('text').help_text,
            'Напишите комментарий...'
        )
