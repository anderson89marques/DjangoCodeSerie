from django.contrib.auth.models import User
from django.core.urlresolvers import resolve, reverse
from django.test import TestCase

from studyproject.boards.models import Board
from studyproject.boards.views import board_topics, home, new_topic


class HomeTest(TestCase):
    def setUp(self):
        self.board = Board.objects.create(
            name="Django", description="Django Board.")
        url = reverse('home')
        self.response = self.client.get(url)

    def test_view_home_status_code(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

    def test_home_url_resoves_home_view(self):
        view = resolve('/')
        self.assertEquals(view.func.view_class, home)

    def test_home_view_contains_link_to_topics_page(self):
        board_topics_url = reverse(
            'board_topics', kwargs={"pk": self.board.pk})
        self.assertContains(self.response, f'href="{board_topics_url}"')
