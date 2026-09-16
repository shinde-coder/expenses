from decimal import Decimal

from django.db.models import Sum

from catalogs.models import CategoryType
from insights.dates import parse_month
from insights.services import _q


def build_settlement(family, month=None):
    start, end, label = parse_month(month)
    rows = list(
        _q(family, start, end)
        .exclude(type=CategoryType.INCOME)
        .values("member_id", "member__display_name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    total = sum((row["total"] or Decimal("0") for row in rows), Decimal("0.00"))
    count = len(rows) or 1
    equal = (total / count).quantize(Decimal("0.01")) if rows else Decimal("0.00")
    members = []
    for row in rows:
        paid = row["total"] or Decimal("0.00")
        members.append(
            {
                "member": str(row["member_id"]),
                "name": row["member__display_name"],
                "paid": paid,
                "percent": (paid / total * Decimal("100")).quantize(Decimal("0.01"))
                if total
                else Decimal("0.00"),
                "equal_share": equal,
                "balance": (paid - equal).quantize(Decimal("0.01")),
            }
        )
    return {
        "month": label,
        "total": total,
        "equal_share": equal,
        "members": members,
        "optional": True,
        "note": "Settlement is optional and separate from normal expense reporting.",
    }
