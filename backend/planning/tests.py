from decimal import Decimal

from rest_framework.test import APITestCase

from core.test_utils import auth_client, catalogs_for
from families.models import FamilyMember
from planning.services import STATUS_NEAR, STATUS_OVER, STATUS_WITHIN, budget_status


class BudgetCalculationTests(APITestCase):
    def test_status_thresholds(self):
        self.assertEqual(budget_status(Decimal("70"), Decimal("100")), STATUS_WITHIN)
        self.assertEqual(budget_status(Decimal("80"), Decimal("100")), STATUS_NEAR)
        self.assertEqual(budget_status(Decimal("101"), Decimal("100")), STATUS_OVER)

    def test_month_budget_and_over_budget(self):
        client, payload = auth_client("budget@example.com")
        family = FamilyMember.objects.get(user__email="budget@example.com").family
        cats = catalogs_for(family)
        saved = client.post(
            "/api/v1/budgets/",
            {
                "month": "2026-09",
                "overall_amount": "27500.00",
                "items": [
                    {"category": str(cats["groceries"].id), "amount": "7000.00"},
                ],
            },
            format="json",
        )
        self.assertEqual(saved.status_code, 200, saved.data)
        client.post(
            "/api/v1/transactions/",
            {
                "type": "EXPENSE",
                "amount": "8000.00",
                "occurred_on": "2026-09-08",
                "category": str(cats["groceries"].id),
                "payment_method": str(cats["upi"].id),
                "member": str(cats["member"].id),
                "description": "Big shop",
            },
            format="json",
        )
        report = client.get("/api/v1/budgets/?month=2026-09")
        groceries = next(
            item
            for item in report.data["data"]["items"]
            if item["category_name"] == "Groceries"
        )
        self.assertEqual(groceries["status"], STATUS_OVER)
        copy = client.post(
            "/api/v1/budgets/copy-previous/",
            {"month": "2026-10"},
            format="json",
        )
        self.assertEqual(copy.status_code, 200)
        overwrite = client.post(
            "/api/v1/budgets/copy-previous/",
            {"month": "2026-10"},
            format="json",
        )
        self.assertEqual(overwrite.status_code, 400)


class RecurringAndGoalTests(APITestCase):
    def test_confirm_recurring_creates_transaction(self):
        client, _ = auth_client("recur@example.com")
        family = FamilyMember.objects.get(user__email="recur@example.com").family
        cats = catalogs_for(family)
        created = client.post(
            "/api/v1/recurring-expenses/",
            {
                "title": "Rent",
                "amount": "15000.00",
                "category": str(cats["groceries"].id),
                "payment_method": str(cats["upi"].id),
                "member": str(cats["member"].id),
                "frequency": "MONTHLY",
                "start_date": "2026-09-01",
                "next_due_date": "2026-09-01",
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        recurring_id = created.data["data"]["id"]
        confirmed = client.post(
            f"/api/v1/recurring-expenses/{recurring_id}/confirm/",
            format="json",
        )
        self.assertEqual(confirmed.status_code, 201, confirmed.data)
        self.assertEqual(confirmed.data["data"]["description"], "Rent")
        listed = client.get("/api/v1/transactions/?month=2026-09")
        self.assertEqual(listed.data["pagination"]["total"], 1)

    def test_goal_progress(self):
        client, _ = auth_client("goal@example.com")
        created = client.post(
            "/api/v1/goals/",
            {
                "name": "Emergency Fund",
                "target_amount": "100000.00",
                "current_amount": "25000.00",
                "target_date": "2026-12-31",
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(
            Decimal(str(created.data["data"]["progress_percent"])), Decimal("25.00")
        )
        self.assertEqual(
            Decimal(str(created.data["data"]["remaining_amount"])), Decimal("75000.00")
        )
        goal_id = created.data["data"]["id"]
        contributed = client.post(
            f"/api/v1/goals/{goal_id}/contribute/",
            {"amount": "5000.00"},
            format="json",
        )
        self.assertEqual(contributed.status_code, 200, contributed.data)
        self.assertEqual(
            Decimal(str(contributed.data["data"]["current_amount"])), Decimal("30000.00")
        )


class BillTests(APITestCase):
    def test_create_and_snooze_bill(self):
        client, _ = auth_client("bills@example.com")
        family = FamilyMember.objects.get(user__email="bills@example.com").family
        cats = catalogs_for(family)
        created = client.post(
            "/api/v1/bills/",
            {
                "title": "Electricity",
                "amount": "1200.00",
                "category": str(cats["groceries"].id),
                "due_date": "2026-09-15",
                "frequency": "MONTHLY",
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        bill_id = created.data["data"]["id"]
        snoozed = client.post(f"/api/v1/bills/{bill_id}/snooze/", {"days": 2}, format="json")
        self.assertEqual(snoozed.status_code, 200, snoozed.data)
        self.assertEqual(snoozed.data["data"]["due_date"], "2026-09-17")
