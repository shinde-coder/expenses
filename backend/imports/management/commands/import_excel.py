from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from families.models import Family
from imports.excel import batch_payload, import_workbook


class Command(BaseCommand):
    help = "Import Monthly_Expenses.xlsx into a family. Invalid rows are reported, never dropped silently."

    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument("--family-id", required=True)
        parser.add_argument("--user-email", required=True)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--lenient",
            action="store_true",
            help="Import rows with empty Paid By or mismatched subcategory instead of rejecting them.",
        )

    def handle(self, *args, **options):
        try:
            family = Family.objects.get(pk=options["family_id"])
            user = User.objects.get(email__iexact=options["user_email"])
        except (Family.DoesNotExist, User.DoesNotExist) as exc:
            raise CommandError(str(exc))
        batch = import_workbook(
            options["path"],
            family=family,
            user=user,
            dry_run=options["dry_run"],
            filename=options["path"],
            lenient=options["lenient"],
        )
        payload = batch_payload(batch)
        self.stdout.write(
            self.style.SUCCESS(
                f"successful={payload['successful_records']} "
                f"failed={payload['failed_records']} "
                f"duplicates={payload['duplicate_records']}"
            )
        )
        for error in payload["errors"]:
            self.stdout.write(f"  row {error['row']}: {error['code']} — {error['reason']}")
