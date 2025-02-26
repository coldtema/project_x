from django.test import SimpleTestCase
from django.urls import reverse


class HomepageTests(SimpleTestCase):
    def test_url_exists_at_correct_location(self):
        response = self.client.get(reverse('hello'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hello')
        self.assertTemplateUsed(response, 'blog/index.html')


class AboutpageTests(SimpleTestCase):
    def test_url_exists_at_correct_location(self):
        response = self.client.get("/blog/about/?name=sbhdrt&age=42")
        self.assertEqual(response.status_code, 200)