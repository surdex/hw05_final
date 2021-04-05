import os
import shutil

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR,
                                           'temp_views_test'))
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_user',
            first_name='Name',
            last_name='Surname'
        )
        cls.subscribed_user = User.objects.create_user(
            username='subscribed_test_user'
        )
        cls.unsubscribed_user = User.objects.create_user(
            username='unsubscribed_test_user'
        )
        cls.group_with_post = Group.objects.create(
            title='Test Group with post',
            slug='test-slug-of-group-with-post',
            description='Test group(1) description',
        )
        cls.group_without_post = Group.objects.create(
            title='Test Group without post',
            slug='test-slug-of-group-without-post',
            description='Test group(2) description',
        )
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
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group_with_post,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            text='Test comment',
            author=cls.user,
            post=cls.post
        )
        Follow.objects.create(author=cls.unsubscribed_user,
                              user=cls.subscribed_user)
        Follow.objects.create(author=cls.user,
                              user=cls.unsubscribed_user)
        kwarg_for_post = {
            'username': PostPagesTests.user.username,
            'post_id': PostPagesTests.post.id
        }
        cls.templates_page_names = {
            'index.html': reverse('index'),
            'group.html': reverse(
                'group',
                kwargs={'slug': PostPagesTests.group_with_post.slug}
            ),
            'post.html': reverse('post', kwargs=kwarg_for_post),
            'profile.html': reverse(
                'profile',
                kwargs={'username': PostPagesTests.user.username}
            )
        }
        cls.template_for_authorized = {
            reverse('new_post'): 'new_post.html',
            reverse('post_edit', kwargs=kwarg_for_post): 'new_post.html',
            reverse('add_comment', kwargs=kwarg_for_post): 'post.html',
            reverse('follow_index'): 'follow.html'
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def context_page_assertions(self, page_object, test_post):
        self.assertEqual(page_object.text, test_post.text)
        self.assertEqual(page_object.pub_date, test_post.pub_date)
        self.assertEqual(page_object.author, test_post.author)
        self.assertEqual(page_object.image, test_post.image)
        self.assertEqual(page_object.id, test_post.id)

    def test_pages_post_correct_template_for_guest(self):
        """URL-адрес использует соответствующий шаблон
        для неавторизованного пользователя."""
        templates_page_names = PostPagesTests.templates_page_names

        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)

                self.assertTemplateUsed(response, template)

    def test_pages_post_correct_template_for_authorized(self):
        """URL-адреса использует соответствующий шаблон
        для авторизованного пользователя."""
        urls_for_authorized = PostPagesTests.template_for_authorized

        for reverse_name, templates in urls_for_authorized.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name,
                                                      follow=True)

                self.assertTemplateUsed(response, templates)

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформированы с правильным контекстом."""
        first_object = 0
        test_post = PostPagesTests.post

        response = self.guest_client.get(reverse('index'))
        page_object = response.context['page'][first_object]

        self.assertIn('page', response.context)
        self.assertContains(response, '<img')
        self.context_page_assertions(page_object, test_post)

    def test_group_with_post_pages_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        group = PostPagesTests.group_with_post
        first_object = 0
        test_post = PostPagesTests.post

        response = self.authorized_client.get(
            self.templates_page_names['group.html']
        )
        page_object = response.context['page'][first_object]
        response_group = response.context['group']

        self.assertIn('page', response.context)
        self.assertIn('group', response.context)
        self.assertContains(response, '<img')
        self.context_page_assertions(page_object, test_post)
        self.assertEqual(response_group.title, group.title)
        self.assertEqual(response_group.slug, group.slug)
        self.assertEqual(response_group.description, group.description)

    def test_group_page_without_post_has_correct_context(self):
        """Созданные посты относятся только к выбранной группе."""
        response = self.authorized_client.get(
            reverse(
                'group',
                kwargs={'slug': PostPagesTests.group_without_post.slug}
            )
        )

        self.assertNotIn(PostPagesTests.post, response.context['page'])

    def test_new_post_page_show_correct_context(self):
        """Шаблон new post сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        response = self.authorized_client.get(reverse('new_post'))

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]

                self.assertIsInstance(form_field, expected)
        self.assertIn('form', response.context)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        templates_page_names = PostPagesTests.templates_page_names
        first_object = 0
        test_post = PostPagesTests.post

        response = self.authorized_client.get(
            templates_page_names['profile.html']
        )
        page_object = response.context['page'][first_object]
        author_object = response.context['author']
        count_posts = response.context['count_posts']

        self.assertIn('page', response.context)
        self.assertIn('author', response.context)
        self.assertIn('count_posts', response.context)
        self.assertContains(response, '<img')
        self.context_page_assertions(page_object, test_post)
        self.assertEqual(author_object.get_full_name(),
                         PostPagesTests.user.get_full_name())
        self.assertEqual(author_object.get_username(),
                         PostPagesTests.user.username)
        self.assertEqual(count_posts, PostPagesTests.user.posts.count())

    def test_post_page_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        templates_page_names = PostPagesTests.templates_page_names
        form_fields = {
            'text': forms.fields.CharField,
        }
        first_object = 0
        test_post = PostPagesTests.post

        response = self.authorized_client.get(
            templates_page_names['post.html']
        )
        page_object = response.context['post']
        author_object = response.context['author']
        comments_object = response.context['comments'][first_object]
        count_posts = response.context['count_posts']
        form_field = response.context['form']

        self.assertIn('post', response.context)
        self.assertIn('author', response.context)
        self.assertIn('comments', response.context)
        self.assertIn('form', response.context)
        self.assertIn('count_posts', response.context)
        self.assertContains(response, '<img')
        self.context_page_assertions(page_object, test_post)
        self.assertEqual(author_object.get_full_name(),
                         PostPagesTests.user.get_full_name())
        self.assertEqual(author_object.get_username(),
                         PostPagesTests.user.username)
        self.assertEqual(comments_object.text,
                         PostPagesTests.comment.text)
        self.assertEqual(comments_object.author.username,
                         PostPagesTests.comment.author.username)
        self.assertEqual(count_posts, PostPagesTests.user.posts.count())
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                self.assertIsInstance(form_field.fields[value], expected)

    def test_paginator_show_correct_context(self):
        """Проверка правильности контекста paginator на всех страницах"""
        view_setting_paginator = 10
        batch_size = 15
        posts = [
            Post(text=f'Infinity text {i}',
                 group=PostPagesTests.group_with_post,
                 author=PostPagesTests.user)
            for i in range(batch_size)
        ]
        Post.objects.bulk_create(posts, batch_size)
        count_all_posts = Post.objects.count()
        pages = {
            '?page=1': view_setting_paginator,
            '?page=2': count_all_posts - view_setting_paginator
        }
        templates_page_names = PostPagesTests.templates_page_names
        pages_with_paginator = ['index.html', 'group.html', 'profile.html']

        for page_urls in pages_with_paginator:
            for number_page, count_post_on_page in pages.items():
                with self.subTest():
                    response = self.guest_client.get(
                        templates_page_names[page_urls] + number_page
                    )
                    count_objects = len(response.context['page'])

                    self.assertEqual(count_objects, count_post_on_page)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом
        для url post_edit."""
        template_page = reverse(
            'post_edit',
            kwargs={
                'username': PostPagesTests.user.username,
                'post_id': PostPagesTests.post.id
            }
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        test_post = PostPagesTests.post

        response = self.authorized_client.get(template_page)
        page_object = response.context['post']

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]

                self.assertIsInstance(form_field, expected)
        self.context_page_assertions(page_object, test_post)

    def test_index_page_cache(self):
        """Проверка кеширования index page"""
        first_response = self.guest_client.get(reverse('index'))
        new_post = Post.objects.create(
            text='Another test publication',
            author=PostPagesTests.user,
        )

        last_response = self.guest_client.get(reverse('index'))

        self.assertEqual(first_response.content, last_response.content,
                         'Проверка кеширования')

        cache.clear()
        response = self.guest_client.get(reverse('index'))

        self.assertIn(new_post, response.context['page'],
                      'Проверка отчистки кеша')

    def test_follow_page_show_correct_context(self):
        """Шаблон follow сформированы с правильным контекстом,
        созданная запись отображается только для подписчика"""
        post = PostPagesTests.post
        subscribed_user = PostPagesTests.subscribed_user
        unsubscribed_user = PostPagesTests.unsubscribed_user
        new_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        new_uploaded = SimpleUploadedFile(
            name='new.gif',
            content=new_gif,
            content_type='image/gif'
        )
        test_post = Post.objects.create(
            text='Another test publication',
            author=unsubscribed_user,
            image=new_uploaded
        )
        first_object = 0

        authorized_subscribed = Client()
        authorized_unsubscribed = Client()
        authorized_subscribed.force_login(subscribed_user)
        authorized_unsubscribed.force_login(unsubscribed_user)
        response_subscribed = authorized_subscribed.get(
            reverse('follow_index')
        )
        response_unsubscribed = authorized_unsubscribed.get(
            reverse('follow_index')
        )
        page_object = response_subscribed.context['page'][first_object]
        page_object_unsub = response_unsubscribed.context['page'][first_object]

        self.assertIn('page', response_subscribed.context)
        self.assertIn('page', response_unsubscribed.context)
        self.assertContains(response_subscribed, '<img')
        self.assertContains(response_unsubscribed, '<img')
        self.context_page_assertions(page_object, test_post)
        self.context_page_assertions(page_object_unsub, post)

    def test_profile_follow(self):
        """Проверка системы подписок profile_follow"""
        unsubscribed_user = PostPagesTests.unsubscribed_user
        subscribed_user = PostPagesTests.subscribed_user

        authorized_unsubscribed = Client()
        authorized_unsubscribed.force_login(unsubscribed_user)
        authorized_unsubscribed.get(
            reverse('profile_follow', kwargs={'username': subscribed_user})
        )

        self.assertTrue(
            Follow.objects.filter(
                author=subscribed_user,
                user=unsubscribed_user
            ).exists()
        )

    def test_profile_unfollow(self):
        """Проверка системы подписок profile_unfollow"""
        unsubscribed_user = PostPagesTests.unsubscribed_user
        subscribed_user = PostPagesTests.subscribed_user

        authorized_subscribed = Client()
        authorized_subscribed.force_login(subscribed_user)
        authorized_subscribed.get(
            reverse('profile_unfollow', kwargs={'username': unsubscribed_user})
        )

        self.assertFalse(
            Follow.objects.filter(
                author=unsubscribed_user,
                user=subscribed_user
            ).exists()
        )
