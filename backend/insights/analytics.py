from decimal import Decimal

from django.db.models import Count, Sum

from catalogs.models import CategoryType
from insights.dates import resolve_period
from insights.services import _q, _safe_change, _sum, category_actuals


def _percent(part, whole):
    if not whole:
        return None
    return (Decimal(part) / Decimal(whole) * Decimal("100")).quantize(Decimal("0.01"))


def build_analytics(family, period="monthly", month=None, date_from=None, date_to=None):
    start, end, prev_start, prev_end, period = resolve_period(
        period, month, date_from, date_to
    )
    days = (end - start).days + 1
    expenses = _sum(_q(family, start, end, CategoryType.EXPENSE))
    income = _sum(_q(family, start, end, CategoryType.INCOME))
    allocated = _sum(_q(family, start, end, CategoryType.SAVING))
    prev_expenses = _sum(_q(family, prev_start, prev_end, CategoryType.EXPENSE))
    change_amount, change_percent = _safe_change(expenses, prev_expenses)

    current_cats = category_actuals(family, start, end, (CategoryType.EXPENSE,))
    previous_cats = category_actuals(family, prev_start, prev_end, (CategoryType.EXPENSE,))
    category_growth = []
    for category_id, data in current_cats.items():
        prev_amount = previous_cats.get(category_id, {}).get("amount", Decimal("0.00"))
        amount_delta, pct = _safe_change(data["amount"], prev_amount)
        category_growth.append(
            {
                "category": str(category_id),
                "category_name": data["name"],
                "icon": data.get("icon", "category"),
                "color": data.get("color", "#7F8C8D"),
                "amount": data["amount"],
                "previous_amount": prev_amount,
                "change_amount": amount_delta,
                "change_percent": pct,
                "percent_of_total": _percent(data["amount"], expenses),
            }
        )
    category_growth.sort(key=lambda row: row["amount"], reverse=True)
    top_category = category_growth[0] if category_growth else None

    daily_rows = list(
        _q(family, start, end, CategoryType.EXPENSE)
        .values("occurred_on")
        .annotate(total=Sum("amount"))
        .order_by("occurred_on")
    )
    highest_day = None
    if daily_rows:
        top = max(daily_rows, key=lambda row: row["total"] or Decimal("0"))
        highest_day = {"date": top["occurred_on"], "amount": top["total"]}

    method_rows = list(
        _q(family, start, end)
        .values("payment_method__name", "payment_method__icon")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )
    member_rows = list(
        _q(family, start, end)
        .values("member__display_name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )

    recurring_amount = Decimal("0.00")
    try:
        from ledger.models import FinancialTransaction

        recurring_amount = (
            FinancialTransaction.objects.filter(
                family=family,
                is_deleted=False,
                recurring_expense__isnull=False,
                occurred_on__gte=start,
                occurred_on__lte=end,
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
    except Exception:
        recurring_amount = Decimal("0.00")

    sufficient = expenses > 0 or income > 0
    insights = []
    if not sufficient:
        insights.append("Not enough data in this period for reliable analytics.")
    else:
        if change_percent is not None:
            direction = "increased" if change_amount > 0 else "decreased"
            insights.append(
                f"Spending {direction} {abs(change_percent)}% compared with the previous period."
            )
        if top_category and top_category["percent_of_total"] is not None:
            insights.append(
                f"{top_category['category_name']} consumed {top_category['percent_of_total']}% of spending."
            )
        if method_rows and expenses:
            lead = method_rows[0]
            share = _percent(lead["total"], expenses)
            if share is not None:
                insights.append(
                    f"{lead['payment_method__name']} was used for {share}% of spending."
                )

    return {
        "period": period,
        "from": start,
        "to": end,
        "sufficient_data": sufficient,
        "total_spending": expenses,
        "total_income": income,
        "allocated_savings": allocated,
        "net_savings": income - expenses,
        "savings_rate": _percent(income - expenses, income) if income else None,
        "spending_growth_amount": change_amount,
        "spending_growth_percent": change_percent,
        "average_daily_spend": (expenses / days).quantize(Decimal("0.01")) if days else Decimal("0.00"),
        "highest_spending_day": highest_day,
        "highest_spending_category": (
            {
                "name": top_category["category_name"],
                "amount": top_category["amount"],
                "percent": top_category["percent_of_total"],
            }
            if top_category
            else None
        ),
        "category_growth": category_growth,
        "payment_method_usage": [
            {
                "name": row["payment_method__name"],
                "icon": row["payment_method__icon"],
                "amount": row["total"],
                "count": row["count"],
                "percent": _percent(row["total"], expenses),
            }
            for row in method_rows
        ],
        "member_spending": [
            {
                "name": row["member__display_name"],
                "amount": row["total"],
                "count": row["count"],
                "percent": _percent(row["total"], expenses + allocated),
            }
            for row in member_rows
        ],
        "daily_spending": [
            {"date": row["occurred_on"], "amount": row["total"]} for row in daily_rows
        ],
        "recurring_expense_amount": recurring_amount,
        "insights": insights,
        "previous_period": {"from": prev_start, "to": prev_end},
    }
