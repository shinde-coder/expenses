from io import BytesIO
from datetime import datetime

from openpyxl import Workbook
from rest_framework.test import APITestCase

from core.test_utils import auth_client
from families.models import FamilyMember
from ledger.models import FinancialTransaction


def _workbook(rows):
    book = Workbook()
    sheet = book.active
    sheet.title = "Transactions"
    sheet.append(
        [
            "Date",
            "Month",
            "Category",
            "Subcategory",
            "Description",
            "Payment Method",
            "Paid By",
            "Amount",
            "Notes",
        ]
    )
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    book.save(buffer)
    buffer.seek(0)
    buffer.name = "Monthly_Expenses.xlsx"
    return buffer


class ExcelImportTests(APITestCase):
    def test_import_reports_invalid_and_imports_valid(self):
        client, _ = auth_client("import@example.com")
        family = FamilyMember.objects.get(user__email="import@example.com").family
        upload = _workbook(
            [
                [datetime(2026, 9, 1), "Sep-2026", "Groceries", "Kirana", "Rice bag", "UPI", "Me", 1680, ""],
                [datetime(2026, 9, 2), "Sep-2026", "Groceries", "Daycare", "Bad pairing", "UPI", "Me", 108, ""],
                [datetime(2026, 9, 1), "Sep-2026", "Groceries", "Snacks", "No payer", "UPI", "", 57, ""],
            ]
        )
        dry = client.post(
            "/api/v1/imports/excel/",
            {"file": upload, "dry_run": "true"},
            format="multipart",
        )
        self.assertEqual(dry.status_code, 200, dry.data)
        self.assertEqual(dry.data["data"]["successful_records"], 1)
        self.assertEqual(dry.data["data"]["failed_records"], 2)
        self.assertEqual(FinancialTransaction.objects.filter(family=family).count(), 0)

        upload.seek(0)
        real = client.post(
            "/api/v1/imports/excel/",
            {"file": upload, "dry_run": "false"},
            format="multipart",
        )
        self.assertEqual(real.status_code, 200)
        self.assertEqual(FinancialTransaction.objects.filter(family=family).count(), 1)
        other, _ = auth_client("otherimport@example.com")
        hidden = other.get(f"/api/v1/imports/{real.data['data']['id']}/")
        self.assertEqual(hidden.status_code, 404)
