from datetime import date, timedelta

from catalogs.lookups import advance_date
from ledger.models import FinancialTransaction
from planning.models import Bill


def computed_status(bill):
    if bill.last_status == Bill.Status.SKIPPED:
        return Bill.Status.SKIPPED
    if bill.last_status == Bill.Status.PAID and bill.last_paid_on == bill.due_date:
        return Bill.Status.PAID
    today = date.today()
    if bill.due_date < today:
        return Bill.Status.OVERDUE
    if bill.due_date == today:
        return Bill.Status.DUE_TODAY
    return Bill.Status.UPCOMING


def advance_bill(bill):
    nxt = advance_date(bill.due_date, bill.frequency)
    if nxt is None:
        bill.is_active = False
        return
    bill.due_date = nxt
    bill.last_status = Bill.Status.UPCOMING


def pay_bill(bill, user, occurred_on=None):
    occurred_on = occurred_on or date.today()
    txn = None
    if bill.auto_post and bill.payment_method_id and bill.member_id:
        txn = FinancialTransaction.objects.create(
            family=bill.family,
            created_by=user,
            type=bill.category.type,
            amount=bill.amount,
            occurred_on=occurred_on,
            category=bill.category,
            payment_method=bill.payment_method,
            member=bill.member,
            description=bill.title,
        )
    bill.last_status = Bill.Status.PAID
    bill.last_paid_on = occurred_on
    advance_bill(bill)
    bill.save()
    return txn


def snooze_bill(bill, days=3):
    bill.due_date = bill.due_date + timedelta(days=max(int(days), 1))
    bill.last_status = Bill.Status.UPCOMING
    bill.save(update_fields=["due_date", "last_status", "updated_at"])
    return bill


def skip_bill(bill):
    bill.last_status = Bill.Status.SKIPPED
    advance_bill(bill)
    bill.save()
    return bill
