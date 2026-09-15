from django.core.management.base import BaseCommand

from catalogs.seeds import seed_system_catalogs


class Command(BaseCommand):
    help = "Idempotently seed system categories, subcategories, and payment methods."

    def handle(self, *args, **options):
        created = seed_system_catalogs()
        self.stdout.write(self.style.SUCCESS(f"Seeded catalogs: {created}"))
