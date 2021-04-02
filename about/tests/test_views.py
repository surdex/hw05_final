from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.reverse_pages = {
            'about/tech.html': reverse('about:tech'),
            'about/author.html': reverse('about:author')
        }

    def test_about_pages_use_correct_template(self):
        """Статические страницы about используют правильные views"""
        for template, reverse_page in self.reverse_pages.items():
            with self.subTest(reverse_page=reverse_page):
                response = self.guest_client.get(reverse_page)
                self.assertTemplateUsed(response, template)
