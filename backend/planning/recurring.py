from datetime import date
from decimal import Decimal

from catalogs.lookups import advance_date
from ledger.models import FinancialTransaction


def advance_due_date(current, frequency):
    nxt = advance_date(current, frequency)
    return current if nxt is None else nxt


def confirm_recurring(recurring, user, occurred_on=None):
    occurred_on = occurred_on or recurring.next_due_date or date.today()
    txn = FinancialTransaction.objects.create(
        family=recurring.family,
        created_by=user,
        type=recurring.category.type,
        amount=recurring.amount,
        occurred_on=occurred_on,
        category=recurring.category,
        subcategory=recurring.subcategory,
        payment_method=recurring.payment_method,
        member=recurring.member,
        description=recurring.title,
        recurring_expense=recurring,
    )
    nxt = advance_due_date(recurring.next_due_date or occurred_on, recurring.frequency)
    if recurring.end_date and nxt > recurring.end_date:
        recurring.is_active = False
    recurring.next_due_date = nxt
    recurring.save(update_fields=["next_due_date", "is_active", "updated_at"])
    return txn


def goal_payload(goal):
    remaining = max(Decimal("0.00"), goal.target_amount - goal.current_amount)
    progress = (
        (goal.current_amount / goal.target_amount * Decimal("100")).quantize(Decimal("0.01"))
        if goal.target_amount
        else Decimal("0.00")
    )
    monthly = None
    if goal.target_date and remaining > 0:
        today = date.today()
        months = (goal.target_date.year - today.year) * 12 + (
            goal.target_date.month - today.month
        )
        months = max(months, 1)
        monthly = (remaining / months).quantize(Decimal("0.01"))
    return {
        "id": str(goal.id),
        "name": goal.name,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount,
        "remaining_amount": remaining,
        "progress_percent": progress,
        "target_date": goal.target_date,
        "description": goal.description,
        "status": goal.status,
        "monthly_contribution_recommendation": monthly,
        "milestones": [
            {
                "percent": pct,
                "amount": (goal.target_amount * pct / Decimal("100")).quantize(Decimal("0.01")),
                "reached": goal.current_amount >= goal.target_amount * pct / Decimal("100"),
            }
            for pct in (25, 50, 75, 100)
        ],
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
    }
