from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.mixins import EnvelopeMixin, FamilyContextMixin
from core.responses import error_response, success_response
from insights.dates import parse_month, previous_month
from insights.services import build_budget_report
from datetime import date

from planning.bills import pay_bill, skip_bill, snooze_bill
from planning.models import (
    Bill,
    CategoryBudget,
    FinancialGoal,
    GoalContribution,
    MonthlyBudget,
    RecurringExpense,
)
from planning.recurring import confirm_recurring, goal_payload
from planning.serializers import (
    BillSerializer,
    BudgetUpsertSerializer,
    CopyBudgetSerializer,
    FinancialGoalSerializer,
    GoalContributeSerializer,
    RecurringExpenseSerializer,
)


class BudgetView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            _, _, label = parse_month(request.query_params.get("month"))
        except ValueError as exc:
            return error_response(str(exc), status=400)
        return success_response(build_budget_report(self.get_family(), label))

    def post(self, request):
        serializer = BudgetUpsertSerializer(
            data=request.data, context={"family": self.get_family()}
        )
        serializer.is_valid(raise_exception=True)
        family = self.get_family()
        start, _, label = parse_month(serializer.validated_data["month"])
        monthly, _ = MonthlyBudget.objects.get_or_create(
            family=family, year_month=start
        )
        if "overall_amount" in serializer.validated_data:
            monthly.overall_amount = serializer.validated_data.get("overall_amount")
            monthly.save(update_fields=["overall_amount", "updated_at"])
        for item in serializer.validated_data.get("items", []):
            CategoryBudget.objects.update_or_create(
                family=family,
                year_month=start,
                category=item["category_obj"],
                defaults={"amount": item["amount"]},
            )
        return success_response(
            build_budget_report(family, label),
            "Budget saved.",
        )


class CopyBudgetView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CopyBudgetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        family = self.get_family()
        start, _, label = parse_month(serializer.validated_data["month"])
        prev_start, _, prev_label = previous_month(start)
        if CategoryBudget.objects.filter(family=family, year_month=start).exists():
            return error_response(
                f"Budgets already exist for {label}. Historical months are never overwritten.",
                status=400,
            )
        previous = CategoryBudget.objects.filter(family=family, year_month=prev_start)
        if not previous.exists():
            return error_response(f"No budget found for {prev_label} to copy.", status=404)
        prev_monthly = MonthlyBudget.objects.filter(
            family=family, year_month=prev_start
        ).first()
        MonthlyBudget.objects.update_or_create(
            family=family,
            year_month=start,
            defaults={
                "overall_amount": prev_monthly.overall_amount if prev_monthly else None
            },
        )
        CategoryBudget.objects.bulk_create(
            [
                CategoryBudget(
                    family=family,
                    year_month=start,
                    category=row.category,
                    amount=row.amount,
                )
                for row in previous
            ]
        )
        return success_response(
            build_budget_report(family, label),
            f"Copied budgets from {prev_label}.",
        )


class FamilyScopedViewSet(EnvelopeMixin, FamilyContextMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            context["family"] = self.get_family()
        return context


class RecurringExpenseViewSet(FamilyScopedViewSet):
    serializer_class = RecurringExpenseSerializer

    def get_queryset(self):
        return RecurringExpense.objects.filter(family=self.get_family()).select_related(
            "category", "subcategory", "payment_method", "member"
        )

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        recurring = self.get_object()
        if not recurring.is_active:
            return error_response("This recurring expense is inactive.", status=400)
        txn = confirm_recurring(recurring, request.user)
        from ledger.serializers import TransactionSerializer

        return success_response(
            TransactionSerializer(txn).data,
            "Transaction created from recurring expense.",
            status=201,
        )


class FinancialGoalViewSet(FamilyScopedViewSet):
    serializer_class = FinancialGoalSerializer

    def get_queryset(self):
        return FinancialGoal.objects.filter(family=self.get_family())

    def retrieve(self, request, *args, **kwargs):
        return success_response(goal_payload(self.get_object()))

    def list(self, request, *args, **kwargs):
        return success_response([goal_payload(item) for item in self.get_queryset()])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        goal = serializer.save()
        return success_response(goal_payload(goal), "Goal created.", status=201)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        goal = serializer.save()
        return success_response(goal_payload(goal), "Goal updated.")

    @action(detail=True, methods=["post"])
    def contribute(self, request, pk=None):
        goal = self.get_object()
        serializer = GoalContributeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]
        withdraw = serializer.validated_data.get("withdraw") is True
        if withdraw and amount > goal.current_amount:
            return error_response("Cannot withdraw more than the current amount.", status=400)
        if withdraw:
            goal.current_amount = goal.current_amount - amount
        else:
            goal.current_amount = goal.current_amount + amount
        if goal.current_amount >= goal.target_amount:
            goal.status = FinancialGoal.Status.ACHIEVED
        elif goal.status == FinancialGoal.Status.ACHIEVED:
            goal.status = FinancialGoal.Status.ACTIVE
        goal.save(update_fields=["current_amount", "status", "updated_at"])
        GoalContribution.objects.create(
            goal=goal,
            family=goal.family,
            created_by=request.user,
            amount=amount,
            is_withdrawal=withdraw,
            note=serializer.validated_data.get("note") or "",
            occurred_on=date.today(),
        )
        return success_response(goal_payload(goal), "Goal updated.")


class BillViewSet(FamilyScopedViewSet):
    serializer_class = BillSerializer

    def get_queryset(self):
        return Bill.objects.filter(family=self.get_family()).select_related(
            "category", "payment_method", "member"
        )

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        bill = self.get_object()
        pay_bill(bill, request.user)
        return success_response(BillSerializer(bill).data, "Bill marked paid.")

    @action(detail=True, methods=["post"])
    def snooze(self, request, pk=None):
        days = request.data.get("days") or 3
        try:
            days = int(days)
        except (TypeError, ValueError):
            days = 3
        snooze_bill(self.get_object(), days)
        return success_response(BillSerializer(self.get_object()).data, "Bill snoozed.")

    @action(detail=True, methods=["post"])
    def skip(self, request, pk=None):
        skip_bill(self.get_object())
        return success_response(BillSerializer(self.get_object()).data, "Bill skipped.")
