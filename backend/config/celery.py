import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("family_expenses")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task
def generate_notifications_task(month=None):
    from notifications.services import generate_all_notifications

    return len(generate_all_notifications(month=month))
