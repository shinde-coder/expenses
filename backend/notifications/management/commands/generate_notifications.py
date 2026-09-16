from django.core.management.base import BaseCommand

from notifications.services import generate_all_notifications


class Command(BaseCommand):
    help = "Create budget, recurring, and goal notification records."

    def add_arguments(self, parser):
        parser.add_argument("--month", help="YYYY-MM")

    def handle(self, *args, **options):
        created = generate_all_notifications(month=options.get("month"))
        self.stdout.write(self.style.SUCCESS(f"Created {len(created)} notifications."))
