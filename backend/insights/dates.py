from calendar import monthrange
from datetime import date, timedelta

from catalogs.lookups import analytics_period_unit, master_codes, master_default


def parse_iso_date(value, field_name="date"):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be YYYY-MM-DD.")


def parse_month(value):
    if not value:
        today = date.today()
        value = today.strftime("%Y-%m")
    try:
        year, month = value.split("-")
        year, month = int(year), int(month)
        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])
    except (ValueError, TypeError):
        raise ValueError("Month must be YYYY-MM.")
    return start, end, f"{year:04d}-{month:02d}"


def previous_month(start):
    prev = start.replace(day=1) - timedelta(days=1)
    prev_start = prev.replace(day=1)
    prev_end = date(prev.year, prev.month, monthrange(prev.year, prev.month)[1])
    return prev_start, prev_end, f"{prev.year:04d}-{prev.month:02d}"


def resolve_period(period="monthly", month=None, date_from=None, date_to=None):
    period = (period or master_default("analytics_period", "monthly") or "monthly").lower()
    if period != "custom":
        allowed = set(master_codes("analytics_period")) or {"weekly", "monthly", "yearly"}
        if period not in allowed:
            raise ValueError("Unknown analytics period.")
    today = date.today()
    unit = analytics_period_unit(period)
    if period == "custom" or unit == "custom":
        if not date_from or not date_to:
            raise ValueError("Custom range requires from and to dates.")
        start = parse_iso_date(date_from, "from")
        end = parse_iso_date(date_to, "to")
        if end < start:
            raise ValueError("to must be on or after from.")
    elif unit in ("week", "weekly"):
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
    elif unit in ("year", "yearly"):
        year = today.year
        if month:
            year = int(month.split("-")[0])
        start = date(year, 1, 1)
        end = date(year, 12, 31)
    else:
        start, end, _ = parse_month(month)
    previous_end = start - timedelta(days=1)
    span = (end - start).days
    previous_start = previous_end - timedelta(days=span)
    return start, end, previous_start, previous_end, period
