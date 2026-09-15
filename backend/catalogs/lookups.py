from datetime import timedelta

from django.db.models import Q
from dateutil.relativedelta import relativedelta

from catalogs.models import Category, MasterValue, PaymentMethod


def masters_payload():
    data = {}
    rows = MasterValue.objects.filter(is_active=True).order_by(
        "group", "sort_order", "label"
    )
    for row in rows:
        data.setdefault(row.group, []).append(
            {
                "code": row.code,
                "label": row.label,
                "icon": row.icon,
                "color": row.color,
                "sort_order": row.sort_order,
                "extra": row.extra or {},
            }
        )
    return data


def master_codes(group):
    return list(
        MasterValue.objects.filter(group=group, is_active=True)
        .order_by("sort_order", "label")
        .values_list("code", flat=True)
    )


def master_row(group, code):
    if not code:
        return None
    return MasterValue.objects.filter(group=group, code=code, is_active=True).first()


def is_valid_master(group, code):
    return master_row(group, code) is not None


def master_default(group, preferred=None):
    if preferred and is_valid_master(group, preferred):
        return preferred
    codes = master_codes(group)
    if preferred and preferred in codes:
        return preferred
    return codes[0] if codes else preferred


def master_extra(group, code):
    row = master_row(group, code)
    return (row.extra if row else {}) or {}


def advance_date(current, frequency_code):
    """Move a date forward using frequency master extra: unit + count."""
    extra = master_extra("frequency", frequency_code)
    unit = (extra.get("unit") or "").lower()
    count = int(extra.get("count") or 1)
    if unit in ("once", "none"):
        return None
    if unit in ("day", "days"):
        return current + timedelta(days=count)
    if unit in ("week", "weeks"):
        return current + timedelta(weeks=count)
    if unit in ("month", "months"):
        return current + relativedelta(months=count)
    if unit in ("year", "years"):
        return current + relativedelta(years=count)
    return current + relativedelta(months=1)


def analytics_period_unit(period):
    extra = master_extra("analytics_period", period)
    return (extra.get("unit") or period or "month").lower()


def find_category(family, name):
    qs = Category.objects.filter(
        Q(family=family) | Q(family__isnull=True),
        name__iexact=name.strip(),
        is_active=True,
    )
    return qs.filter(family=family).first() or qs.filter(family__isnull=True).first()


def find_payment_method(family, name):
    qs = PaymentMethod.objects.filter(
        Q(family=family) | Q(family__isnull=True),
        name__iexact=name.strip(),
        is_active=True,
    )
    return qs.filter(family=family).first() or qs.filter(family__isnull=True).first()


def resolve_relationship(label):
    text = (label or "").strip().lower()
    if not text:
        return _default_relationship()
    for row in MasterValue.objects.filter(group="relationship", is_active=True):
        aliases = [a.lower() for a in (row.extra or {}).get("aliases", [])]
        if text in {row.code.lower(), row.label.lower(), *aliases}:
            return row.code
    return _default_relationship()


def _default_relationship():
    other = MasterValue.objects.filter(
        group="relationship", code="OTHER", is_active=True
    ).first()
    if other:
        return other.code
    first = (
        MasterValue.objects.filter(group="relationship", is_active=True)
        .order_by("sort_order")
        .first()
    )
    return first.code if first else "OTHER"
