from decimal import Decimal

from rest_framework.test import APITestCase

from catalogs.models import Category, CategoryType
from core.test_utils import auth_client, catalogs_for
from families.models import FamilyMember
from ledger.models import FinancialTransaction


class TransactionTests(APITestCase):
    def setUp(self):
        self.client_a, self.payload_a = auth_client("a@example.com")
        self.client_b, self.payload_b = auth_client("b@example.com")
        self.family_a = FamilyMember.objects.get(
            user__email="a@example.com"
        ).family
        self.cats = catalogs_for(self.family_a)

    def _expense_payload(self, **overrides):
        data = {
            "type": "EXPENSE",
            "amount": "1680.00",
            "occurred_on": "2026-09-01",
            "category": str(self.cats["groceries"].id),
            "subcategory": str(self.cats["kirana"].id),
            "payment_method": str(self.cats["upi"].id),
            "member": str(self.cats["member"].id),
            "description": "Rice bag",
        }
        data.update(overrides)
        return data

    def test_create_edit_delete_and_monthly_filter(self):
        created = self.client_a.post(
            "/api/v1/transactions/", self._expense_payload(), format="json"
        )
        self.assertEqual(created.status_code, 201, created.data)
        txn_id = created.data["data"]["id"]
        self.assertEqual(created.data["data"]["category_name"], "Groceries")

        listed = self.client_a.get("/api/v1/transactions/?month=2026-09")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data["pagination"]["total"], 1)

        patched = self.client_a.patch(
            f"/api/v1/transactions/{txn_id}/",
            {"amount": "1700.00"},
            format="json",
        )
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(Decimal(patched.data["data"]["amount"]), Decimal("1700.00"))

        deleted = self.client_a.delete(f"/api/v1/transactions/{txn_id}/")
        self.assertEqual(deleted.status_code, 200)
        self.assertTrue(
            FinancialTransaction.objects.get(id=txn_id).is_deleted
        )
        listed = self.client_a.get("/api/v1/transactions/")
        self.assertEqual(listed.data["pagination"]["total"], 0)

    def test_duplicate_creates_copy(self):
        created = self.client_a.post(
            "/api/v1/transactions/",
            self._expense_payload(tags=["kirana"]),
            format="json",
        )
        txn_id = created.data["data"]["id"]
        duplicated = self.client_a.post(f"/api/v1/transactions/{txn_id}/duplicate/")
        self.assertEqual(duplicated.status_code, 201, duplicated.data)
        listed = self.client_a.get("/api/v1/transactions/?month=2026-09")
        self.assertEqual(listed.data["pagination"]["total"], 2)

    def test_amount_must_be_positive(self):
        response = self.client_a.post(
            "/api/v1/transactions/",
            self._expense_payload(amount="0"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data["success"])

    def test_subcategory_must_match_category(self):
        utilities = Category.objects.get(
            family=None, name="Utilities", type=CategoryType.EXPENSE
        )
        electricity = utilities.subcategories.get(name="Electricity")
        response = self.client_a.post(
            "/api/v1/transactions/",
            self._expense_payload(subcategory=str(electricity.id)),
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_family_isolation(self):
        created = self.client_a.post(
            "/api/v1/transactions/", self._expense_payload(), format="json"
        )
        txn_id = created.data["data"]["id"]
        other = self.client_b.get(f"/api/v1/transactions/{txn_id}/")
        self.assertEqual(other.status_code, 404)
        listed = self.client_b.get("/api/v1/transactions/")
        self.assertEqual(listed.data["pagination"]["total"], 0)

    def test_pagination(self):
        for i in range(21):
            self.client_a.post(
                "/api/v1/transactions/",
                self._expense_payload(description=f"Item {i}", amount="10.00"),
                format="json",
            )
        page1 = self.client_a.get("/api/v1/transactions/?page=1&page_size=20")
        self.assertEqual(len(page1.data["data"]), 20)
        self.assertTrue(page1.data["pagination"]["has_next"])
        self.assertEqual(page1.data["pagination"]["total"], 21)
