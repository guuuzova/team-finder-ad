from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from users.models import User

from .models import STATUS_CLOSED, STATUS_OPEN, Project

TEST_PASSWORD = "ComplexPass123!"
OWNER_EMAIL = "owner@example.com"
OTHER_EMAIL = "other@example.com"
OWNER_NAME = "Owner"
OWNER_SURNAME = "One"
OTHER_NAME = "Other"
OTHER_SURNAME = "Two"
PROJECT_NAME = "Test project"
PROJECT_DESCRIPTION = "desc"

HOME_URL = "/"
HOME_REDIRECT_URL = "/projects/list/"

ROUTE_PROJECT_LIST = "projects:list"
ROUTE_TOGGLE_FAVORITE = "projects:toggle_favorite"
ROUTE_TOGGLE_PARTICIPATE = "projects:toggle_participate"
ROUTE_COMPLETE = "projects:complete"

RESPONSE_STATUS_KEY = "status"
RESPONSE_FAVORITED_KEY = "favorited"
RESPONSE_PARTICIPANT_KEY = "participant"
RESPONSE_PROJECT_STATUS_KEY = "project_status"


class ProjectsFlowTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email=OWNER_EMAIL,
            password=TEST_PASSWORD,
            name=OWNER_NAME,
            surname=OWNER_SURNAME,
        )
        self.other = User.objects.create_user(
            email=OTHER_EMAIL,
            password=TEST_PASSWORD,
            name=OTHER_NAME,
            surname=OTHER_SURNAME,
        )
        self.project = Project.objects.create(
            name=PROJECT_NAME,
            description=PROJECT_DESCRIPTION,
            owner=self.owner,
            status=STATUS_OPEN,
        )
        self.project.participants.add(self.owner)
        self.client = Client()

    def test_home_redirects_to_list(self):
        response = self.client.get(HOME_URL)
        self.assertRedirects(
            response, HOME_REDIRECT_URL, fetch_redirect_response=False
        )

    def test_project_list_accessible_anonymously(self):
        response = self.client.get(reverse(ROUTE_PROJECT_LIST))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_toggle_favorite_requires_auth(self):
        url = reverse(ROUTE_TOGGLE_FAVORITE, args=[self.project.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_toggle_favorite_adds_and_removes(self):
        self.client.login(email=OTHER_EMAIL, password=TEST_PASSWORD)
        url = reverse(ROUTE_TOGGLE_FAVORITE, args=[self.project.id])
        response = self.client.post(url)
        self.assertEqual(response.json()[RESPONSE_FAVORITED_KEY], True)
        response = self.client.post(url)
        self.assertEqual(response.json()[RESPONSE_FAVORITED_KEY], False)

    def test_complete_project_by_owner(self):
        self.client.login(email=OWNER_EMAIL, password=TEST_PASSWORD)
        url = reverse(ROUTE_COMPLETE, args=[self.project.id])
        response = self.client.post(url)
        self.assertEqual(response.json()[RESPONSE_PROJECT_STATUS_KEY], STATUS_CLOSED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, STATUS_CLOSED)

    def test_toggle_participate(self):
        self.client.login(email=OTHER_EMAIL, password=TEST_PASSWORD)
        url = reverse(ROUTE_TOGGLE_PARTICIPATE, args=[self.project.id])
        response = self.client.post(url)
        self.assertTrue(response.json()[RESPONSE_PARTICIPANT_KEY])
        self.assertIn(self.other, self.project.participants.all())
