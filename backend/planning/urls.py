from django.urls import include, path
from rest_framework.routers import DefaultRouter

from planning.views import (
    BillViewSet,
    BudgetView,
    CopyBudgetView,
    FinancialGoalViewSet,
    RecurringExpenseViewSet,
)

router = DefaultRouter()
router.register("recurring-expenses", RecurringExpenseViewSet, basename="recurring-expenses")
router.register("goals", FinancialGoalViewSet, basename="goals")
router.register("bills", BillViewSet, basename="bills")

urlpatterns = [
    path("budgets/", BudgetView.as_view(), name="budgets"),
    path("budgets/copy-previous/", CopyBudgetView.as_view(), name="budgets-copy"),
    path("", include(router.urls)),
]
