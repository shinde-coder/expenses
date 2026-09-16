from datetime import date, timedelta

from django.utils import timezone

from insights.dates import parse_month
from insights.services import build_budget_report
from notifications.models import AppNotification
from planning.models import FinancialGoal, RecurringExpense
from planning.services import STATUS_NEAR, STATUS_OVER


def _notify(family, ntype, title, body, payload, dedupe_key):
    existing = AppNotification.objects.filter(family=family, dedupe_key=dedupe_key).first()
    if existing:
        return existing, False
    note = AppNotification.objects.create(
        family=family,
        type=ntype,
        title=title,
        body=body,
        payload=payload,
        dedupe_key=dedupe_key,
        sent_at=timezone.now(),
    )
    return note, True


def generate_family_notifications(family, month=None):
    created = []
    start, end, label = parse_month(month)
    report = build_budget_report(family, label)
    if report["status"] == STATUS_OVER:
        note, was = _notify(
            family,
            AppNotification.Type.BUDGET_EXCEEDED,
            "Budget exceeded",
            f"Overall spending has exceeded the {label} budget.",
            {"month": label, "status": report["status"]},
            f"budget-over:{family.id}:{label}",
        )
        if was:
            created.append(note)
    elif report["status"] == STATUS_NEAR:
        note, was = _notify(
            family,
            AppNotification.Type.BUDGET_NEAR,
            "Budget approaching limit",
            f"Overall budget for {label} is {report['used_percent']}% used.",
            {"month": label, "used_percent": str(report["used_percent"])},
            f"budget-near:{family.id}:{label}",
        )
        if was:
            created.append(note)

    for item in report["items"]:
        if item["status"] == STATUS_NEAR:
            note, was = _notify(
                family,
                AppNotification.Type.BUDGET_NEAR,
                f"{item['category_name']} budget is nearly used",
                f"{item['category_name']} budget is {item['used_percent']}% used.",
                {"month": label, "category": item["category"]},
                f"budget-near:{family.id}:{label}:{item['category']}",
            )
            if was:
                created.append(note)
        elif item["status"] == STATUS_OVER:
            note, was = _notify(
                family,
                AppNotification.Type.BUDGET_EXCEEDED,
                f"{item['category_name']} is over budget",
                f"{item['category_name']} spending exceeded its {label} budget.",
                {"month": label, "category": item["category"]},
                f"budget-over:{family.id}:{label}:{item['category']}",
            )
            if was:
                created.append(note)

    soon = date.today() + timedelta(days=2)
    due_items = RecurringExpense.objects.filter(
        family=family, is_active=True, next_due_date__lte=soon
    )
    for item in due_items:
        when = "today" if item.next_due_date == date.today() else item.next_due_date.isoformat()
        if item.next_due_date == date.today() + timedelta(days=1):
            when = "tomorrow"
        note, was = _notify(
            family,
            AppNotification.Type.RECURRING_DUE,
            f"{item.title} is due {when}",
            f"Rent-style reminder: {item.title} of ₹{item.amount} is due {when}.",
            {"recurring_id": str(item.id)},
            f"recurring:{item.id}:{item.next_due_date.isoformat()}",
        )
        if was:
            created.append(note)

    for goal in FinancialGoal.objects.filter(family=family, status=FinancialGoal.Status.ACTIVE):
        if goal.target_date and goal.target_date <= date.today() + timedelta(days=30):
            note, was = _notify(
                family,
                AppNotification.Type.GOAL_REMINDER,
                f"Goal reminder: {goal.name}",
                f"{goal.name} is due by {goal.target_date.isoformat()}.",
                {"goal_id": str(goal.id)},
                f"goal:{goal.id}:{goal.target_date.isoformat()}",
            )
            if was:
                created.append(note)
    return created


def generate_all_notifications(month=None):
    from families.models import Family

    created = []
    for family in Family.objects.all():
        created.extend(generate_family_notifications(family, month=month))
    return created
