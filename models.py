from django.test import TestCase
from rest_framework.test import APIClient


class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user_and_returns_tokens(self):
        res = self.client.post("/api/v1/auth/register/", {
            "first_name": "A", "last_name": "B", "email": "a@b.com",
            "phone": "03001112222", "password": "verysecure123",
        }, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertIn("access", res.json())

    def test_duplicate_email_is_rejected(self):
        payload = {"first_name": "A", "last_name": "B", "email": "dup@b.com", "phone": "03001112223", "password": "verysecure123"}
        self.client.post("/api/v1/auth/register/", payload, format="json")
        res = self.client.post("/api/v1/auth/register/", {**payload, "phone": "03001112224"}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_login_with_wrong_password_fails(self):
        self.client.post("/api/v1/auth/register/", {
            "first_name": "A", "last_name": "B", "email": "login@b.com",
            "phone": "03001112225", "password": "verysecure123",
        }, format="json")
        res = self.client.post("/api/v1/auth/login/", {"email_or_phone": "login@b.com", "password": "wrong"}, format="json")
        self.assertEqual(res.status_code, 401)
