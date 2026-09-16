from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Sum

from catalogs.models import CategoryType
from insights.dates import parse_month, previous_month
from insights.services import _q, _sum, build_budget_report, category_actuals
from ledger.models import FinancialTransaction
from planning.models import RecurringExpense
from planning.services import financial_health, savings_rate


def _insight(code, title, body, *, action=None, evidence=None):
    return {
        "code": code,
        "title": title,
        "body": body,
        "action": action or {},
        "evidence": evidence or {},
    }


def build_structured_insights(family, month_str):
    start, end, label = parse_month(month_str)
    prev_start, prev_end, prev_label = previous_month(start)
    expenses = _sum(_q(family, start, end, CategoryType.EXPENSE))
    income = _sum(_q(family, start, end, CategoryType.INCOME))
    savings = _sum(_q(family, start, end, CategoryType.SAVING))
    budget = build_budget_report(family, label)
    insights = []

    current = category_actuals(family, start, end, (CategoryType.EXPENSE,))
    previous = category_actuals(family, prev_start, prev_end, (CategoryType.EXPENSE,))
    for category_id, data in current.items():
        prev_amount = previous.get(category_id, {}).get("amount", Decimal("0.00"))
        amount = data["amount"]
        if prev_amount > 0 and amount > prev_amount * Decimal("1.15"):
            pct = ((amount - prev_amount) / prev_amount * Decimal("100")).quantize(
                Decimal("0.01")
            )
            insights.append(
                _insight(
                    "SPENDING_SPIKE",
                    f"{data['name']} is up {pct}%",
                    f"{data['name']} is {pct}% higher than {prev_label}.",
                    action={"screen": "transactions", "category": str(category_id)},
                    evidence={
                        "category": data["name"],
                        "current": amount,
                        "previous": prev_amount,
                    },
                )
            )
        budget_item = next(
            (
                item
                for item in budget["items"]
                if item["category"] == str(category_id) and item["budget"]
            ),
            None,
        )
        if budget_item and budget_item["status"] in {"NEAR_LIMIT", "OVER_BUDGET"}:
            remaining = budget_item["difference"]
            insights.append(
                _insight(
                    "BUDGET_RISK",
                    f"{data['name']} budget risk",
                    (
                        f"You have ₹{remaining} left in {data['name']}."
                        if remaining and remaining > 0
                        else f"{data['name']} is over its monthly budget."
                    ),
                    action={"screen": "budgets", "category": str(category_id)},
                    evidence=budget_item,
                )
            )

    rate = savings_rate(income, savings)
    if rate is not None:
        prev_income = _sum(_q(family, prev_start, prev_end, CategoryType.INCOME))
        prev_savings = _sum(_q(family, prev_start, prev_end, CategoryType.SAVING))
        prev_rate = savings_rate(prev_income, prev_savings)
        if prev_rate is not None and rate > prev_rate:
            insights.append(
                _insight(
                    "POSITIVE_SAVINGS",
                    "Savings rate improved",
                    f"Your savings rate improved from {prev_rate}% to {rate}%.",
                    action={"screen": "goals"},
                    evidence={"current": rate, "previous": prev_rate},
                )
            )

    due = RecurringExpense.objects.filter(
        family=family, is_active=True, next_due_date__lte=end
    ).count()
    if due:
        insights.append(
            _insight(
                "RECURRING_DUE",
                "Recurring payments due",
                f"{due} recurring payment(s) are due this month.",
                action={"screen": "recurring"},
                evidence={"count": due},
            )
        )

    unusual = (
        _q(family, start, end, CategoryType.EXPENSE)
        .order_by("-amount")
        .first()
    )
    if unusual and expenses:
        avg = expenses / max(_q(family, start, end, CategoryType.EXPENSE).count(), 1)
        if unusual.amount > avg * Decimal("3"):
            insights.append(
                _insight(
                    "UNUSUAL_TRANSACTION",
                    "Unusually large expense",
                    f"{unusual.description or unusual.category_name_snapshot} "
                    f"(₹{unusual.amount}) is much larger than your usual spend.",
                    action={"screen": "transaction", "id": str(unusual.id)},
                    evidence={"id": str(unusual.id), "amount": unusual.amount},
                )
            )

    if not insights:
        insights.append(
            _insight(
                "EMPTY",
                "Keep tracking",
                "Add a few more transactions to unlock spending insights.",
                action={"screen": "add"},
            )
        )
    return insights


def build_calendar(family, month_str):
    start, end, label = parse_month(month_str)
    days = (end - start).days + 1
    expenses = _sum(_q(family, start, end, CategoryType.EXPENSE))
    daily_limit = (expenses / days).quantize(Decimal("0.01")) if expenses else Decimal("0")
    budget = build_budget_report(family, label)
    if budget["overall_amount"]:
        daily_limit = (Decimal(budget["overall_amount"]) / days).quantize(Decimal("0.01"))

    by_day = {}
    rows = (
        FinancialTransaction.objects.filter(
            family=family,
            is_deleted=False,
            occurred_on__gte=start,
            occurred_on__lte=end,
        )
        .values("occurred_on", "type")
        .annotate(total=Sum("amount"))
    )
    for row in rows:
        day = row["occurred_on"].isoformat()
        bucket = by_day.setdefault(
            day,
            {
                "date": day,
                "income": Decimal("0.00"),
                "expenses": Decimal("0.00"),
                "savings": Decimal("0.00"),
                "net": Decimal("0.00"),
                "count": 0,
            },
        )
        amount = row["total"] or Decimal("0.00")
        if row["type"] == CategoryType.INCOME:
            bucket["income"] += amount
        elif row["type"] == CategoryType.SAVING:
            bucket["savings"] += amount
        else:
            bucket["expenses"] += amount

    counts = (
        FinancialTransaction.objects.filter(
            family=family,
            is_deleted=False,
            occurred_on__gte=start,
            occurred_on__lte=end,
        )
        .values("occurred_on")
        .annotate(total=Sum("amount"))
    )
    count_map = {
        row["occurred_on"].isoformat(): FinancialTransaction.objects.filter(
            family=family,
            is_deleted=False,
            occurred_on=row["occurred_on"],
        ).count()
        for row in counts
    }

    items = []
    for offset in range(days):
        current = date(start.year, start.month, offset + 1)
        key = current.isoformat()
        bucket = by_day.get(
            key,
            {
                "date": key,
                "income": Decimal("0.00"),
                "expenses": Decimal("0.00"),
                "savings": Decimal("0.00"),
            },
        )
        net = bucket["income"] - bucket["expenses"] - bucket["savings"]
        intensity = 0
        if daily_limit and bucket["expenses"]:
            intensity = min(int(bucket["expenses"] / daily_limit * 3), 3)
        items.append(
            {
                **bucket,
                "net": net,
                "count": count_map.get(key, 0),
                "daily_limit": daily_limit,
                "remaining_allowance": daily_limit - bucket["expenses"],
                "intensity": intensity,
            }
        )
    return {"month": label, "daily_limit": daily_limit, "days": items}


def month_forecast(family, month_str):
    start, end, label = parse_month(month_str)
    today = date.today()
    if today < start:
        elapsed = 1
    elif today > end:
        elapsed = (end - start).days + 1
    else:
        elapsed = (today - start).days + 1
    days = (end - start).days + 1
    expenses = _sum(_q(family, start, end, CategoryType.EXPENSE))
    pace = (expenses / elapsed).quantize(Decimal("0.01")) if elapsed else Decimal("0.00")
    projected = (pace * days).quantize(Decimal("0.01"))
    return {
        "month": label,
        "elapsed_days": elapsed,
        "days_in_month": days,
        "current_expenses": expenses,
        "projected_month_end": projected,
        "is_estimate": True,
    }


def today_snapshot(family, month_str):
    start, end, label = parse_month(month_str)
    today = date.today()
    if not (start <= today <= end):
        today = start if date.today() < start else end
    spent = _sum(
        FinancialTransaction.objects.filter(
            family=family,
            is_deleted=False,
            type=CategoryType.EXPENSE,
            occurred_on=today,
        )
    )
    count = FinancialTransaction.objects.filter(
        family=family, is_deleted=False, occurred_on=today
    ).count()
    days = monthrange(start.year, start.month)[1]
    budget = build_budget_report(family, label)
    suggested = None
    if budget["overall_amount"]:
        suggested = (Decimal(budget["overall_amount"]) / days).quantize(Decimal("0.01"))
    remaining = (suggested - spent) if suggested is not None else None
    return {
        "date": today.isoformat(),
        "spent": spent,
        "count": count,
        "suggested_limit": suggested,
        "remaining": remaining,
    }


def dashboard_extras(family, month_str, dashboard):
    income = dashboard["total_income"]
    savings = dashboard["allocated_savings"]
    rate = savings_rate(income, savings)
    forecast = month_forecast(family, month_str)
    health = financial_health(
        budget_status_value=dashboard["budget_status"],
        savings_rate_value=rate,
        expenses=dashboard["total_expenses"],
        income=income,
    )
    return {
        "savings_rate": rate,
        "health_status": health,
        "today": today_snapshot(family, month_str),
        "forecast": forecast,
        "insight_cards": build_structured_insights(family, month_str),
    }
