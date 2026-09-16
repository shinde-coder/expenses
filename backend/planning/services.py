from decimal import Decimal

from django.conf import settings

NEAR_LIMIT_RATIO = Decimal(getattr(settings, "BUDGET_NEAR_LIMIT_RATIO", "0.80"))

STATUS_WITHIN = "WITHIN_BUDGET"
STATUS_NEAR = "NEAR_LIMIT"
STATUS_OVER = "OVER_BUDGET"
STATUS_NO_BUDGET = "NO_BUDGET"

HEALTH_HEALTHY = "HEALTHY"
HEALTH_WATCH = "WATCH"
HEALTH_OVERSPENDING = "OVERSPENDING"

SAVINGS_RATE_HEALTHY = Decimal(getattr(settings, "SAVINGS_RATE_HEALTHY", "10"))


def budget_status(actual, budget):
    actual = Decimal(actual or 0)
    if budget is None:
        return STATUS_NO_BUDGET
    budget = Decimal(budget)
    if budget == 0:
        return STATUS_OVER if actual > 0 else STATUS_WITHIN
    ratio = actual / budget
    if ratio > 1:
        return STATUS_OVER
    if ratio >= NEAR_LIMIT_RATIO:
        return STATUS_NEAR
    return STATUS_WITHIN


def used_percent(actual, budget):
    actual = Decimal(actual or 0)
    if not budget:
        return None
    return (actual / Decimal(budget) * Decimal("100")).quantize(Decimal("0.01"))


def savings_rate(income, allocated_savings):
    income = Decimal(income or 0)
    allocated = Decimal(allocated_savings or 0)
    if income <= 0:
        return None
    return (allocated / income * Decimal("100")).quantize(Decimal("0.01"))


def financial_health(*, budget_status_value, savings_rate_value, expenses, income):
    expenses = Decimal(expenses or 0)
    income = Decimal(income or 0)
    if budget_status_value == STATUS_OVER or (income > 0 and expenses > income):
        return HEALTH_OVERSPENDING
    if budget_status_value == STATUS_NEAR:
        return HEALTH_WATCH
    if savings_rate_value is not None and savings_rate_value < SAVINGS_RATE_HEALTHY:
        return HEALTH_WATCH
    return HEALTH_HEALTHY
