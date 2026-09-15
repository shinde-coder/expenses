try:
    from .celery import app as celery_app
except Exception:  # Celery/Redis are optional for local CRUD
    celery_app = None

__all__ = ("celery_app",)
