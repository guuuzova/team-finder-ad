from django.test import Client, TestCase
from django.urls import reverse

from users.models import User

from .models import STATUS_CLOSED, STATUS_OPEN, Project

TEST_PASSWORD = "ComplexPass123!"


class ProjectsFlowTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password=TEST_PASSWORD,
            name="Owner",
            surname="One",
        )
        self.other = User.objects.create_user(
            email="other@example.com",
            password=TEST_PASSWORD,
            name="Other",
            surname="Two",
        )
        self.project = Project.objects.create(
            name="Test project",
            description="desc",
            owner=self.owner,
            status=STATUS_OPEN,
        )
        self.project.participants.add(self.owner)
        self.client = Client()

    def test_home_redirects_to_list(self):
        response = self.client.get("/")
        self.assertRedirects(response, "/projects/list/", fetch_redirect_response=False)

    def test_project_list_accessible_anonymously(self):
        response = self.client.get(reverse("projects:list"))
        self.assertEqual(response.status_code, 200)

    def test_toggle_favorite_requires_auth(self):
        url = reverse("projects:toggle_favorite", args=[self.project.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

    def test_toggle_favorite_adds_and_removes(self):
        self.client.login(email="other@example.com", password=TEST_PASSWORD)
        url = reverse("projects:toggle_favorite", args=[self.project.id])
        response = self.client.post(url)
        self.assertEqual(response.json()["favorited"], True)
        response = self.client.post(url)
        self.assertEqual(response.json()["favorited"], False)

    def test_complete_project_by_owner(self):
        self.client.login(email="owner@example.com", password=TEST_PASSWORD)
        url = reverse("projects:complete", args=[self.project.id])
        response = self.client.post(url)
        self.assertEqual(response.json()["project_status"], STATUS_CLOSED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, STATUS_CLOSED)

    def test_toggle_participate(self):
        self.client.login(email="other@example.com", password=TEST_PASSWORD)
        url = reverse("projects:toggle_participate", args=[self.project.id])
        response = self.client.post(url)
        self.assertTrue(response.json()["participant"])
        self.assertIn(self.other, self.project.participants.all())
