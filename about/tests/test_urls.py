from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.reverse_pages = {
            'about/tech.html': '/about/tech/',
            'about/author.html': '/about/author/'
        }

    def test_about_page_accessible_by_name(self):
        """URL, генерируемый страницами about, доступен."""
        for reverse_page in self.reverse_pages.values():
            with self.subTest(reverse_page=reverse_page):
                response = self.guest_client.get(reverse_page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_pages_use_correct_template(self):
        """При запросе к статичным страницам about
        применяется соответствующий html шаблон."""
        for template, reverse_page in self.reverse_pages.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.guest_client.get(reverse_page)
                self.assertTemplateUsed(response, template)
