import os
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR,
                                           'temp_forms_test'))
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-group',
            description='Description test group',
        )
        cls.new_group = Group.objects.create(
            title='New test group',
            slug='new-test-group',
            description='Description test group',
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTest.user)

    def test_create_post(self):
        """Валидная форма создаёт запись в Post"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post_data = {
            'text': 'New test text',
            'image': uploaded,
            'group': PostFormTest.group.id,
        }

        response = self.authorized_client.post(
            reverse('new_post'),
            data=post_data,
            follow=True,
        )

        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='New test text',
                author=PostFormTest.user,
                group=PostFormTest.group.id,
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post"""
        post_id = PostFormTest.post.id
        post_data = {
            'text': 'New test text',
            'group': PostFormTest.new_group.id,
        }
        kwargs_post = {
            'username': PostFormTest.user.username,
            'post_id': post_id,
        }

        response = self.authorized_client.post(
            reverse('post_edit', kwargs=kwargs_post),
            data=post_data,
            follow=True,
        )

        self.assertRedirects(response,
                             reverse('post', kwargs=kwargs_post))
        self.assertEqual(Post.objects.get(id=post_id).text, post_data['text'])
        self.assertEqual(Post.objects.get(id=post_id).group.id,
                         post_data['group'])

    def test_add_comment(self):
        """Валидная форма создаёт comment к post"""
        comment_count = Comment.objects.count()
        comment_data = {
            'text': 'New test comment',
        }
        kwargs_post = {
            'username': PostFormTest.user.username,
            'post_id': PostFormTest.post.id,
        }

        response = self.authorized_client.post(
            reverse('add_comment', kwargs=kwargs_post),
            data=comment_data,
            follow=True,
        )

        self.assertRedirects(response, reverse('post', kwargs=kwargs_post))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='New test comment',
                author=PostFormTest.user,
                post=PostFormTest.post.id,
            ).exists()
        )

    # Какой смысл в этом тесте, если стоит декоратор login_required
    # и фактически производится проверка его работы?
    def test_create_comment_guest(self):
        """Неавторизованный пользователь не может создать comment в Post."""
        form_data = {
            'text': 'Test news comment',
        }
        kwargs_post = {
            'username': PostFormTest.user.username,
            'post_id': PostFormTest.post.id,
        }

        self.guest_client.post(
            reverse('add_comment', kwargs=kwargs_post),
            data=form_data,
            follow=True
        )
        self.assertFalse(
            Comment.objects.filter(
                text='Test news comment',
                author=PostFormTest.user,
                post=PostFormTest.post.id
            ).exists()
        )
