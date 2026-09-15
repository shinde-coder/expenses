from rest_framework.test import APITestCase

from accounts.models import User
from families.models import FamilyMember


class AuthTests(APITestCase):
    def test_register_login_profile_and_refresh(self):
        register = self.client.post(
            "/api/v1/auth/register/",
            {"email": "dad@example.com", "password": "StrongPass123", "name": "Dad"},
            format="json",
        )
        self.assertEqual(register.status_code, 201)
        self.assertTrue(register.data["success"])
        self.assertIn("access", register.data["data"])
        self.assertEqual(register.data["data"]["family"]["currency"], "INR")
        self.assertTrue(
            FamilyMember.objects.filter(
                user__email="dad@example.com",
                relationship=FamilyMember.Relationship.SELF,
            ).exists()
        )

        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "dad@example.com", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)
        access = login.data["data"]["access"]
        refresh = login.data["data"]["refresh"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        profile = self.client.get("/api/v1/auth/profile/")
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.data["data"]["user"]["email"], "dad@example.com")

        refresh_resp = self.client.post(
            "/api/v1/auth/refresh/", {"refresh": refresh}, format="json"
        )
        self.assertEqual(refresh_resp.status_code, 200)
        self.assertTrue(refresh_resp.data["success"])

    def test_invalid_login(self):
        self.client.post(
            "/api/v1/auth/register/",
            {"email": "dad@example.com", "password": "StrongPass123", "name": "Dad"},
            format="json",
        )
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "dad@example.com", "password": "wrong-password"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "Invalid email or password.")

    def test_forgot_and_reset_password(self):
        self.client.post(
            "/api/v1/auth/register/",
            {"email": "mom@example.com", "password": "StrongPass123", "name": "Mom"},
            format="json",
        )
        forgot = self.client.post(
            "/api/v1/auth/forgot-password/",
            {"email": "mom@example.com"},
            format="json",
        )
        self.assertEqual(forgot.status_code, 200)
        uid = forgot.data["data"]["uid"]
        token = forgot.data["data"]["token"]
        reset = self.client.post(
            "/api/v1/auth/reset-password/",
            {"uid": uid, "token": token, "new_password": "NewStrong123"},
            format="json",
        )
        self.assertEqual(reset.status_code, 200)
        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "mom@example.com", "password": "NewStrong123"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)

    def test_change_password(self):
        register = self.client.post(
            "/api/v1/auth/register/",
            {"email": "me@example.com", "password": "StrongPass123", "name": "Me"},
            format="json",
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {register.data['data']['access']}"
        )
        changed = self.client.post(
            "/api/v1/change-password/",
            {"current_password": "StrongPass123", "new_password": "EvenStronger123"},
            format="json",
        )
        # path is under /api/v1/auth/
        self.assertEqual(changed.status_code, 404)
        changed = self.client.post(
            "/api/v1/auth/change-password/",
            {"current_password": "StrongPass123", "new_password": "EvenStronger123"},
            format="json",
        )
        self.assertEqual(changed.status_code, 200)
        self.assertTrue(User.objects.get(email="me@example.com").check_password("EvenStronger123"))
