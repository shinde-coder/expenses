from rest_framework.test import APITestCase

from core.test_utils import auth_client
from families.models import FamilyMember


class InvitationTests(APITestCase):
    def test_invite_and_accept_moves_user(self):
        owner, _ = auth_client("owner@example.com")
        guest, _ = auth_client("guest@example.com")
        created = owner.post("/api/v1/families/invitations/", format="json")
        self.assertEqual(created.status_code, 201, created.data)
        code = created.data["data"]["code"]
        accepted = guest.post(
            "/api/v1/families/invitations/accept/",
            {"code": code},
            format="json",
        )
        self.assertEqual(accepted.status_code, 200, accepted.data)
        guest_member = FamilyMember.objects.get(user__email="guest@example.com", is_active=True)
        owner_family = FamilyMember.objects.get(user__email="owner@example.com").family
        self.assertEqual(guest_member.family_id, owner_family.id)
        self.assertEqual(guest_member.role, FamilyMember.Role.EDITOR)
