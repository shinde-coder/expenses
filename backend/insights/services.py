from decimal import Decimal

from django.db.models import Count, Sum

from catalogs.models import Category, CategoryType
from insights.dates import parse_month, previous_month
from ledger.models import FinancialTransaction
from planning.models import CategoryBudget, MonthlyBudget
from planning.services import budget_status, used_percent


def _q(family, start, end, txn_type=None):
    qs = FinancialTransaction.objects.filter(
        family=family,
        is_deleted=False,
        occurred_on__gte=start,
        occurred_on__lte=end,
    )
    if txn_type:
        qs = qs.filter(type=txn_type)
    return qs


def _sum(qs):
    return qs.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")


def category_actuals(family, start, end, txn_types=None):
    qs = _q(family, start, end)
    if txn_types:
        qs = qs.filter(type__in=txn_types)
    rows = qs.values("category_id", "category_name_snapshot").annotate(total=Sum("amount"))
    categories = Category.objects.in_bulk([row["category_id"] for row in rows if row["category_id"]])
    result = {}
    for row in rows:
        category = categories.get(row["category_id"])
        result[row["category_id"]] = {
            "name": row["category_name_snapshot"],
            "amount": row["total"] or Decimal("0.00"),
            "icon": category.icon if category else "category",
            "color": category.color if category else "#7F8C8D",
        }
    return result


def build_budget_report(family, month_str):
    start, end, label = parse_month(month_str)
    monthly = MonthlyBudget.objects.filter(family=family, year_month=start).first()
    budgets = {
        row.category_id: row
        for row in CategoryBudget.objects.filter(family=family, year_month=start).select_related(
            "category"
        )
    }
    spendable = (CategoryType.EXPENSE, CategoryType.SAVING)
    actuals = category_actuals(family, start, end, spendable)

    visible_ids = set(budgets) | set(actuals)
    categories = {
        c.id: c
        for c in Category.objects.filter(id__in=visible_ids)
    } if visible_ids else {}

    items = []
    total_budget = Decimal("0.00")
    total_actual = Decimal("0.00")
    for category_id in visible_ids:
        budget_row = budgets.get(category_id)
        actual = actuals.get(category_id, {}).get("amount", Decimal("0.00"))
        category = categories.get(category_id)
        name = (
            category.name
            if category
            else actuals.get(category_id, {}).get("name", "Unknown")
        )
        budget_amount = budget_row.amount if budget_row else None
        if budget_amount is not None:
            total_budget += budget_amount
        total_actual += actual
        difference = (budget_amount - actual) if budget_amount is not None else None
        items.append(
            {
                "category": str(category_id) if category_id else None,
                "category_name": name,
                "icon": category.icon if category else "category",
                "color": category.color if category else "#7F8C8D",
                "budget": budget_amount,
                "actual": actual,
                "difference": difference,
                "used_percent": used_percent(actual, budget_amount),
                "status": budget_status(actual, budget_amount),
            }
        )
    items.sort(key=lambda row: row["category_name"])

    overall = monthly.overall_amount if monthly else None
    if overall is None:
        overall = total_budget if total_budget > 0 else None
    remaining = (overall - total_actual) if overall is not None else None

    return {
        "month": label,
        "overall_amount": overall,
        "total_budget": total_budget,
        "total_actual": total_actual,
        "remaining": remaining,
        "used_percent": used_percent(total_actual, overall),
        "status": budget_status(total_actual, overall),
        "items": items,
    }


def _safe_change(current, previous):
    current = Decimal(current or 0)
    previous = Decimal(previous or 0)
    change_amount = current - previous
    if previous == 0:
        change_percent = None if current == 0 else None
        if current > 0:
            change_percent = None
        return change_amount, change_percent
    change_percent = (change_amount / previous * Decimal("100")).quantize(Decimal("0.01"))
    return change_amount, change_percent


def build_dashboard(family, month_str):
    start, end, label = parse_month(month_str)
    prev_start, prev_end, prev_label = previous_month(start)
    days = (end - start).days + 1

    expenses = _sum(_q(family, start, end, CategoryType.EXPENSE))
    income = _sum(_q(family, start, end, CategoryType.INCOME))
    allocated_savings = _sum(_q(family, start, end, CategoryType.SAVING))
    prev_expenses = _sum(_q(family, prev_start, prev_end, CategoryType.EXPENSE))

    budget = build_budget_report(family, label)
    net_savings = income - expenses
    count = _q(family, start, end).count()
    avg_daily = (expenses / days).quantize(Decimal("0.01")) if days else Decimal("0.00")

    top_category = None
    cat_rows = (
        _q(family, start, end, CategoryType.EXPENSE)
        .values("category_id", "category_name_snapshot")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    if cat_rows:
        row = cat_rows[0]
        top_category = {
            "id": str(row["category_id"]),
            "name": row["category_name_snapshot"],
            "amount": row["total"],
        }

    top_expense = (
        _q(family, start, end, CategoryType.EXPENSE)
        .order_by("-amount", "-occurred_on")
        .select_related("category", "member", "payment_method")
        .first()
    )

    from ledger.serializers import TransactionSerializer

    recent = (
        _q(family, start, end)
        .select_related("category", "subcategory", "payment_method", "member")
        .order_by("-occurred_on", "-created_at")[:8]
    )

    change_amount, change_percent = _safe_change(expenses, prev_expenses)

    category_breakdown = []
    expense_actuals = category_actuals(family, start, end, (CategoryType.EXPENSE,))
    for category_id, data in expense_actuals.items():
        amount = data["amount"]
        pct = (amount / expenses * Decimal("100")).quantize(Decimal("0.01")) if expenses else Decimal("0.00")
        category_breakdown.append(
            {
                "category": str(category_id),
                "category_name": data["name"],
                "icon": data.get("icon", "category"),
                "color": data.get("color", "#7F8C8D"),
                "amount": amount,
                "percent": pct,
            }
        )
    category_breakdown.sort(key=lambda row: row["amount"], reverse=True)

    method_rows = (
        _q(family, start, end)
        .values("payment_method__name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )
    member_rows = (
        _q(family, start, end)
        .values("member__display_name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )
    daily_rows = (
        _q(family, start, end, CategoryType.EXPENSE)
        .values("occurred_on")
        .annotate(total=Sum("amount"))
        .order_by("occurred_on")
    )

    insights = []
    if expenses == 0 and income == 0:
        insights.append("No transactions recorded for this month.")
    if top_category and expenses:
        insights.append(
            f"{top_category['name']} is your highest expense category this month."
        )
    if budget["status"] == "OVER_BUDGET":
        insights.append("You are over the overall budget for this month.")
    elif budget["status"] == "NEAR_LIMIT":
        insights.append("You are approaching the overall budget limit.")
    if change_percent is not None:
        direction = "increased" if change_amount > 0 else "decreased"
        insights.append(
            f"Spending {direction} {abs(change_percent)}% vs {prev_label}."
        )

    top_expense_data = None
    if top_expense:
        top_expense_data = {
            "id": str(top_expense.id),
            "description": top_expense.description or top_expense.category_name_snapshot,
            "amount": top_expense.amount,
            "occurred_on": top_expense.occurred_on,
        }

    payload = {
        "month": label,
        "total_income": income,
        "total_expenses": expenses,
        "allocated_savings": allocated_savings,
        "net_savings": net_savings,
        "total_budget": budget["total_budget"],
        "remaining_budget": budget["remaining"],
        "budget_used_percent": budget["used_percent"],
        "budget_status": budget["status"],
        "transaction_count": count,
        "average_daily_spend": avg_daily,
        "top_category": top_category,
        "top_expense": top_expense_data,
        "vs_previous_month": {
            "month": prev_label,
            "expenses": prev_expenses,
            "change_amount": change_amount,
            "change_percent": change_percent,
        },
        "category_breakdown": category_breakdown,
        "payment_method_breakdown": [
            {
                "name": row["payment_method__name"],
                "amount": row["total"],
                "count": row["count"],
            }
            for row in method_rows
        ],
        "member_breakdown": [
            {
                "name": row["member__display_name"],
                "amount": row["total"],
                "count": row["count"],
            }
            for row in member_rows
        ],
        "daily_spending": [
            {"date": row["occurred_on"], "amount": row["total"]} for row in daily_rows
        ],
        "recent_transactions": TransactionSerializer(recent, many=True).data,
        "budget": budget,
        "insights": insights,
        "upcoming_recurring": _upcoming_recurring(family),
    }
    from insights.intelligence import dashboard_extras

    extras = dashboard_extras(family, label, payload)
    payload.update(extras)
    return payload


def _upcoming_recurring(family, limit=5):
    from datetime import date

    from planning.models import RecurringExpense

    items = RecurringExpense.objects.filter(
        family=family, is_active=True
    ).order_by("next_due_date")[:limit]
    return [
        {
            "id": str(item.id),
            "title": item.title,
            "amount": item.amount,
            "next_due_date": item.next_due_date,
            "frequency": item.frequency,
        }
        for item in items
        if item.next_due_date and item.next_due_date >= date.today()
    ]


def build_summary(family, month_str):
    dashboard = build_dashboard(family, month_str)
    return {
        "month": dashboard["month"],
        "total_expenses": dashboard["total_expenses"],
        "total_income": dashboard["total_income"],
        "total_savings": dashboard["allocated_savings"],
        "net_savings": dashboard["net_savings"],
        "total_budget": dashboard["total_budget"],
        "remaining_budget": dashboard["remaining_budget"],
        "transaction_count": dashboard["transaction_count"],
        "average_daily_spend": dashboard["average_daily_spend"],
        "highest_spending_category": dashboard["top_category"],
        "highest_single_expense": dashboard["top_expense"],
        "categories": dashboard["budget"]["items"],
        "payment_methods": dashboard["payment_method_breakdown"],
        "members": dashboard["member_breakdown"],
    }
