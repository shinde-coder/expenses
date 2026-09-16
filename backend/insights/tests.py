from decimal import Decimal

from rest_framework.test import APITestCase

from core.test_utils import auth_client, catalogs_for
from families.models import FamilyMember


class DashboardTests(APITestCase):
    def test_monthly_totals_and_empty_previous_month(self):
        client, _ = auth_client("dash@example.com")
        family = FamilyMember.objects.get(user__email="dash@example.com").family
        cats = catalogs_for(family)
        client.post(
            "/api/v1/transactions/",
            {
                "type": "EXPENSE",
                "amount": "1680.00",
                "occurred_on": "2026-09-01",
                "category": str(cats["groceries"].id),
                "payment_method": str(cats["upi"].id),
                "member": str(cats["member"].id),
                "description": "Rice bag",
            },
            format="json",
        )
        client.post(
            "/api/v1/transactions/",
            {
                "type": "INCOME",
                "amount": "50000.00",
                "occurred_on": "2026-09-01",
                "category": str(cats["salary"].id),
                "payment_method": str(cats["upi"].id),
                "member": str(cats["member"].id),
                "description": "Salary",
            },
            format="json",
        )
        dash = client.get("/api/v1/dashboard/?month=2026-09")
        self.assertEqual(dash.status_code, 200)
        data = dash.data["data"]
        self.assertEqual(Decimal(str(data["total_expenses"])), Decimal("1680.00"))
        self.assertEqual(Decimal(str(data["total_income"])), Decimal("50000.00"))
        self.assertEqual(Decimal(str(data["net_savings"])), Decimal("48320.00"))
        self.assertEqual(data["top_category"]["name"], "Groceries")
        self.assertIsNone(data["vs_previous_month"]["change_percent"])

        summary = client.get("/api/v1/summaries/?month=2026-09")
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.data["data"]["transaction_count"], 2)

        analytics = client.get("/api/v1/analytics/?period=monthly&month=2026-09")
        self.assertEqual(analytics.status_code, 200)
        self.assertTrue(analytics.data["data"]["sufficient_data"])
        self.assertEqual(
            Decimal(str(analytics.data["data"]["total_spending"])), Decimal("1680.00")
        )
        self.assertIsNone(analytics.data["data"]["spending_growth_percent"])

        empty = client.get("/api/v1/analytics/?period=monthly&month=2026-01")
        self.assertFalse(empty.data["data"]["sufficient_data"])

        report = client.get("/api/v1/reports/monthly/?month=2026-09")
        self.assertEqual(report.status_code, 200)
        export = client.post(
            "/api/v1/reports/category/export/",
            {"month": "2026-09", "format": "csv"},
            format="json",
        )
        self.assertEqual(export.status_code, 200)
        self.assertIn("text/csv", export["Content-Type"])

        settlement = client.get("/api/v1/settlement/?month=2026-09")
        self.assertEqual(settlement.status_code, 200)
        self.assertTrue(settlement.data["data"]["optional"])
        self.assertEqual(
            Decimal(str(settlement.data["data"]["total"])), Decimal("1680.00")
        )
        self.assertIn(dash.data["data"]["health_status"], {"HEALTHY", "WATCH", "OVERSPENDING"})
        calendar = client.get("/api/v1/calendar/?month=2026-09")
        self.assertEqual(calendar.status_code, 200)
        self.assertEqual(len(calendar.data["data"]["days"]), 30)
