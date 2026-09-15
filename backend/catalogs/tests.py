from datetime import date

from rest_framework.test import APITestCase

from catalogs.lookups import advance_date, find_category, resolve_relationship
from catalogs.models import MasterValue
from core.test_utils import auth_client


class MastersApiTests(APITestCase):
    def test_masters_come_from_database(self):
        client, _ = auth_client("masters@example.com")
        response = client.get("/api/v1/masters/")
        self.assertEqual(response.status_code, 200, response.data)
        data = response.data["data"]
        type_codes = [row["code"] for row in data["transaction_type"]]
        self.assertEqual(type_codes, ["EXPENSE", "INCOME", "SAVING"])
        self.assertTrue(any(row["code"] == "DAD" for row in data["relationship"]))
        self.assertTrue(any(row["code"] == "MONTHLY" for row in data["frequency"]))
        self.assertTrue(any(row["code"] == "ONCE" for row in data["frequency"]))
        self.assertTrue(any(row["code"] == "monthly" for row in data["report_type"]))

    def test_new_master_row_is_returned(self):
        MasterValue.objects.create(
            group="relationship",
            code="UNCLE",
            label="Uncle",
            icon="person",
            sort_order=20,
        )
        client, _ = auth_client("uncle@example.com")
        response = client.get("/api/v1/masters/")
        codes = [row["code"] for row in response.data["data"]["relationship"]]
        self.assertIn("UNCLE", codes)

    def test_member_can_use_relationship_from_masters(self):
        MasterValue.objects.create(
            group="relationship",
            code="UNCLE",
            label="Uncle",
            icon="person",
            sort_order=20,
        )
        client, _ = auth_client("uncle-member@example.com")
        response = client.post(
            "/api/v1/members/",
            {"display_name": "Ravi", "relationship": "UNCLE"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["data"]["relationship"], "UNCLE")

    def test_unknown_transaction_type_is_rejected(self):
        client, _ = auth_client("bad-type@example.com")
        response = client.post(
            "/api/v1/categories/",
            {"name": "Bonus", "type": "NOT_A_TYPE"},
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.data)

    def test_resolve_relationship_uses_aliases_from_db(self):
        self.assertEqual(resolve_relationship("wife"), "SPOUSE")
        self.assertEqual(resolve_relationship("Me"), "SELF")

    def test_find_category_uses_system_catalog(self):
        client, payload = auth_client("cat@example.com")
        from families.models import FamilyMember

        family = FamilyMember.objects.get(user__email="cat@example.com").family
        groceries = find_category(family, "Groceries")
        self.assertIsNotNone(groceries)
        self.assertEqual(groceries.name, "Groceries")

    def test_advance_date_uses_frequency_master_extra(self):
        start = date(2026, 1, 15)
        self.assertEqual(advance_date(start, "WEEKLY"), date(2026, 1, 22))
        self.assertEqual(advance_date(start, "QUARTERLY"), date(2026, 4, 15))
        self.assertIsNone(advance_date(start, "ONCE"))
