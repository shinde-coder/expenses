from rest_framework.test import APITestCase

from core.test_utils import auth_client, catalogs_for
from families.models import FamilyMember
from notifications.models import AppNotification


class NotificationTests(APITestCase):
    def test_budget_over_notification(self):
        client, _ = auth_client("note@example.com")
        family = FamilyMember.objects.get(user__email="note@example.com").family
        cats = catalogs_for(family)
        client.post(
            "/api/v1/budgets/",
            {
                "month": "2026-09",
                "items": [{"category": str(cats["groceries"].id), "amount": "100.00"}],
            },
            format="json",
        )
        client.post(
            "/api/v1/transactions/",
            {
                "type": "EXPENSE",
                "amount": "200.00",
                "occurred_on": "2026-09-01",
                "category": str(cats["groceries"].id),
                "payment_method": str(cats["upi"].id),
                "member": str(cats["member"].id),
                "description": "Over",
            },
            format="json",
        )
        generated = client.post(
            "/api/v1/notifications/generate/",
            {"month": "2026-09"},
            format="json",
        )
        self.assertEqual(generated.status_code, 200)
        self.assertTrue(
            AppNotification.objects.filter(
                family=family, type=AppNotification.Type.BUDGET_EXCEEDED
            ).exists()
        )
        listed = client.get("/api/v1/notifications/")
        self.assertGreaterEqual(listed.data["pagination"]["total"], 1)
