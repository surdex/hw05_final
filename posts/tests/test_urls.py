from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.user_without_posts = User.objects.create_user(
            username='user_without_posts'
        )
        cls.group = Group.objects.create(
            title='Test Group',
            slug='test-slug-of-group',
            description='Test group description',
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group,
        )
        cls.urls_for_guest = [
            '/',
            f'/group/{cls.group.slug}/',
            f'/{cls.user.username}/',
            f'/{cls.user.username}/{cls.post.id}/',
        ]
        cls.urls_for_authorized = [
            '/new/',
            '/follow/',
            f'/{cls.user.username}/{cls.post.id}/edit/',
        ]
        cls.redir_dict_for_authorized = {
            f'/{cls.user.username}/{cls.post.id}/edit/':
                f'/{cls.user.username}/{cls.post.id}/',
            f'/{cls.user.username}/{cls.post.id}/comment/':
                f'/{cls.user.username}/{cls.post.id}/',
            f'/{cls.user.username}/follow/': f'/{cls.user.username}/',
            f'/{cls.user.username}/unfollow/': f'/{cls.user.username}/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.user)
        self.authorized_client_without_posts = Client()
        self.authorized_client_without_posts.force_login(
            StaticURLTests.user_without_posts
        )

    def test_URls_exists_at_desired_location_for_guest(self):
        """Страницы доступные любому пользователю."""
        for url in StaticURLTests.urls_for_guest:
            with self.subTest(url=url):
                response = self.guest_client.get(url)

                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_URls_exists_at_desired_location_only_for_authorized(self):
        """Страницы доступные только авторизованному автору поста."""
        for url in StaticURLTests.urls_for_authorized:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)

                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_anonymous_client(self):
        """Страницы перенаправляющие анонимного пользователя."""
        login = reverse('login')
        urls_for_authorized = StaticURLTests.urls_for_authorized
        redir_dict_for_authorized = StaticURLTests.redir_dict_for_authorized
        urls = urls_for_authorized + list(redir_dict_for_authorized.keys())

        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)

                self.assertRedirects(response, f'{login}?next={url}')

    def test_urls_redirect_authorized_client(self):
        """Страницы перенаправляющие авторизованного пользователя"""
        redir_dict_for_authorized = StaticURLTests.redir_dict_for_authorized

        for url, redir_url in redir_dict_for_authorized.items():
            with self.subTest(url=url):
                response = self.authorized_client_without_posts.get(
                    url,
                    follow=True
                )

                self.assertRedirects(response, redir_url)

    def test_urls_uses_correct_template(self):
        """URL-адреса использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'index.html',
            f'/group/{StaticURLTests.group.slug}/': 'group.html',
            f'/{StaticURLTests.user.username}/{StaticURLTests.post.id}/edit/':
                'new_post.html',
            '/new/': 'new_post.html',
            f'/{StaticURLTests.user}/{StaticURLTests.post.id}/': 'post.html',
            f'/{StaticURLTests.user.username}/': 'profile.html',
            '/follow/': 'follow.html'
        }

        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)

                self.assertTemplateUsed(response, template)

    def test_return_not_found_code(self):
        """Сервер возвращает код 404, если страница не существует"""
        response = self.guest_client.get('/non/existen/page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
