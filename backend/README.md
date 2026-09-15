# Family Monthly Expense Tracker

Flutter + Django REST app converted from `Monthly_Expenses.xlsx`.

## Backend

```bash
cd backend
python manage.py migrate
python manage.py runserver
python manage.py test
python manage.py createsuperuser
python manage.py generate_notifications --month 2026-09
python manage.py import_excel "C:\Users\LohiyaGroup\Downloads\Monthly_Expenses.xlsx" --family-id <uuid> --user-email you@example.com --dry-run
```

API base: `http://127.0.0.1:8000/api/v1/`  
Admin: `http://127.0.0.1:8000/admin/`

Local default is SQLite. For PostgreSQL + Redis:

```
DATABASE_URL=postgres://family_expenses:family_expenses@127.0.0.1:5433/family_expenses
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
```

then `docker compose up -d` from the repo root.

Optional Celery worker (reminders / heavy reports):

```bash
celery -A config worker -l info
```

Notifications also work without Celery via `generate_notifications` or `POST /api/v1/notifications/generate/`.

## Mobile

```bash
cd mobile
flutter pub get
flutter run
```

Android emulator uses `http://10.0.2.2:8000`. Windows/web use `http://127.0.0.1:8000`.

Pull-to-refresh on Home flushes the offline expense outbox.

## Production checklist

- Set `DJANGO_DEBUG=false` and a strong `DJANGO_SECRET_KEY`
- Use PostgreSQL, not SQLite
- Restrict `DJANGO_ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
- Serve behind HTTPS; do not enable `CORS_ALLOW_ALL_ORIGINS`
- Rotate JWT secrets and keep short access-token lifetimes
- Confirm every financial queryset is family-scoped (covered by tests)
- Turn off password-reset token echo (`DEBUG` / test only)
- Run `manage.py generate_notifications` or Celery on a schedule
- Back up the database before Excel imports
- Store Flutter tokens only in secure storage (already used)
- Do not commit `.env` or `db.sqlite3`
