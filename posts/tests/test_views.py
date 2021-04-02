from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_user',
            first_name='Name',
            last_name='Surname'
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
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group_with_post,
        )
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
        cls.template_new_post = {
            'new_post': reverse('new_post'),
            'edit_post': reverse('post_edit', kwargs=kwarg_for_post)
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def context_page_assertions(self, page_object):
        self.assertEqual(page_object.text, PostPagesTests.post.text)
        self.assertEqual(page_object.pub_date, PostPagesTests.post.pub_date)
        self.assertEqual(page_object.author, PostPagesTests.post.author)
        self.assertEqual(page_object.id, PostPagesTests.post.id)

    def test_pages_post_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = PostPagesTests.templates_page_names

        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)

                self.assertTemplateUsed(response, template)

    def test_pages_post_correct_template_new_post(self):
        """URL-адреса использует шаблон new_post.html."""
        pages_name = PostPagesTests.template_new_post

        for reverse_name in pages_name.values():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)

                self.assertTemplateUsed(response, 'new_post.html')

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформированы с правильным контекстом."""
        response = self.guest_client.get(reverse('index'))
        page_object = response.context['page'][0]

        self.assertIn('page', response.context)
        self.context_page_assertions(page_object)

    def test_group_with_post_pages_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        group = PostPagesTests.group_with_post

        response = self.authorized_client.get(
            self.templates_page_names['group.html']
        )
        page_object = response.context['page'][0]
        response_group = response.context['group']

        self.assertIn('page', response.context)
        self.assertIn('group', response.context)
        self.context_page_assertions(page_object)
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

        response = self.authorized_client.get(
            templates_page_names['profile.html']
        )
        page_object = response.context['page'][0]
        author_object = response.context['author']
        count_posts = response.context['count_posts']

        self.assertIn('page', response.context)
        self.assertIn('author', response.context)
        self.assertIn('count_posts', response.context)
        self.context_page_assertions(page_object)
        self.assertEqual(author_object.get_full_name(),
                         PostPagesTests.user.get_full_name())
        self.assertEqual(author_object.get_username(),
                         PostPagesTests.user.username)
        self.assertEqual(count_posts, PostPagesTests.user.posts.count())

    def test_post_page_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        templates_page_names = PostPagesTests.templates_page_names

        response = self.authorized_client.get(
            templates_page_names['post.html']
        )
        page_object = response.context['post']
        author_object = response.context['author']
        count_posts = response.context['count_posts']

        self.assertIn('post', response.context)
        self.assertIn('author', response.context)
        self.assertIn('count_posts', response.context)
        self.context_page_assertions(page_object)
        self.assertEqual(author_object.get_full_name(),
                         PostPagesTests.user.get_full_name())
        self.assertEqual(author_object.get_username(),
                         PostPagesTests.user.username)
        self.assertEqual(count_posts, PostPagesTests.user.posts.count())

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
        """Отредактированные посты сохранены в БД."""
        template_page = PostPagesTests.template_new_post
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        response = self.authorized_client.get(template_page['edit_post'])
        page_object = response.context['post']

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]

                self.assertIsInstance(form_field, expected)
        self.context_page_assertions(page_object)
