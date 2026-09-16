from django.contrib import admin

from planning.models import (
    Bill,
    CategoryBudget,
    FinancialGoal,
    GoalContribution,
    MonthlyBudget,
    RecurringExpense,
    SubcategoryBudget,
)


@admin.register(MonthlyBudget)
class MonthlyBudgetAdmin(admin.ModelAdmin):
    list_display = ("family", "year_month", "overall_amount")
    list_filter = ("year_month",)
    search_fields = ("family__name",)


@admin.register(CategoryBudget)
class CategoryBudgetAdmin(admin.ModelAdmin):
    list_display = ("family", "year_month", "category", "amount")
    list_filter = ("year_month",)
    search_fields = ("family__name", "category__name")
    autocomplete_fields = ("family", "category")


@admin.register(SubcategoryBudget)
class SubcategoryBudgetAdmin(admin.ModelAdmin):
    list_display = ("family", "year_month", "subcategory", "amount")
    list_filter = ("year_month",)
    autocomplete_fields = ("family", "subcategory")


@admin.register(RecurringExpense)
class RecurringExpenseAdmin(admin.ModelAdmin):
    list_display = ("title", "family", "amount", "frequency", "next_due_date", "is_active")
    list_filter = ("frequency", "is_active")
    search_fields = ("title", "family__name")


@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ("name", "family", "target_amount", "current_amount", "status")
    list_filter = ("status",)
    search_fields = ("name", "family__name")


@admin.register(GoalContribution)
class GoalContributionAdmin(admin.ModelAdmin):
    list_display = ("goal", "amount", "is_withdrawal", "occurred_on")


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ("title", "family", "amount", "due_date", "last_status", "is_active")
    list_filter = ("last_status", "is_active", "frequency")
