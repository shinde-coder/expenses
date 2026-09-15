from django.apps import AppConfig


class CatalogsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalogs"

    def ready(self):
        from django.db.models.signals import post_migrate

        from catalogs.signals import seed_catalogs_after_migrate

        post_migrate.connect(seed_catalogs_after_migrate, sender=self)
