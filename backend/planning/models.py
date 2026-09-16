from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from catalogs.models import Category, SubCategory
from core.models import TimeStampedUUIDModel
from families.models import Family


class MonthlyBudget(TimeStampedUUIDModel):
    family = models.ForeignKey(
        Family, on_delete=models.CASCADE, related_name="monthly_budgets"
    )
    year_month = models.DateField(help_text="First day of the month.")
    overall_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        unique_together = ("family", "year_month")
        ordering = ["-year_month"]
        indexes = [models.Index(fields=["family", "year_month"])]

    def __str__(self):
        return f"{self.family} {self.year_month:%Y-%m}"


class CategoryBudget(TimeStampedUUIDModel):
    family = models.ForeignKey(
        Family, on_delete=models.CASCADE, related_name="category_budgets"
    )
    year_month = models.DateField()
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="budgets"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        unique_together = ("family", "year_month", "category")
        ordering = ["category__name"]
        indexes = [models.Index(fields=["family", "year_month"])]

    def __str__(self):
        return f"{self.category.name} {self.year_month:%Y-%m} {self.amount}"


class SubcategoryBudget(TimeStampedUUIDModel):
    family = models.ForeignKey(
        Family, on_delete=models.CASCADE, related_name="subcategory_budgets"
    )
    year_month = models.DateField()
    subcategory = models.ForeignKey(
        SubCategory, on_delete=models.PROTECT, related_name="budgets"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )

    class Meta:
        unique_together = ("family", "year_month", "subcategory")


class RecurringExpense(TimeStampedUUIDModel):
    class Frequency(models.TextChoices):
        DAILY = "DAILY", "Daily"
        WEEKLY = "WEEKLY", "Weekly"
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        YEARLY = "YEARLY", "Yearly"

    family = models.ForeignKey(
        Family, on_delete=models.CASCADE, related_name="recurring_expenses"
    )
    title = models.CharField(max_length=120)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="recurring_expenses"
    )
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="recurring_expenses",
    )
    payment_method = models.ForeignKey(
        "catalogs.PaymentMethod",
        on_delete=models.PROTECT,
        related_name="recurring_expenses",
    )
    member = models.ForeignKey(
        "families.FamilyMember",
        on_delete=models.PROTECT,
        related_name="recurring_expenses",
    )
    frequency = models.CharField(max_length=16)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_due_date = models.DateField()
    is_active = models.BooleanField(default=True)
    auto_create = models.BooleanField(default=False)

    class Meta:
        ordering = ["next_due_date", "title"]
        indexes = [
            models.Index(fields=["family", "is_active", "next_due_date"]),
        ]

    def __str__(self):
        return self.title


class FinancialGoal(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ACHIEVED = "ACHIEVED", "Achieved"
        ABANDONED = "ABANDONED", "Abandoned"

    family = models.ForeignKey(
        Family, on_delete=models.CASCADE, related_name="goals"
    )
    name = models.CharField(max_length=120)
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    current_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    target_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, default="")
    status = models.CharField(max_length=16, default=Status.ACTIVE)

    class Meta:
        ordering = ["status", "target_date", "name"]

    def __str__(self):
        return self.name


class GoalContribution(TimeStampedUUIDModel):
    goal = models.ForeignKey(
        FinancialGoal, on_delete=models.CASCADE, related_name="contributions"
    )
    family = models.ForeignKey(
        Family, on_delete=models.CASCADE, related_name="goal_contributions"
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="goal_contributions",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    is_withdrawal = models.BooleanField(default=False)
    note = models.CharField(max_length=255, blank=True, default="")
    occurred_on = models.DateField()

    class Meta:
        ordering = ["-occurred_on", "-created_at"]


class Bill(TimeStampedUUIDModel):
    class Frequency(models.TextChoices):
        ONCE = "ONCE", "One time"
        WEEKLY = "WEEKLY", "Weekly"
        MONTHLY = "MONTHLY", "Monthly"
        QUARTERLY = "QUARTERLY", "Quarterly"
        YEARLY = "YEARLY", "Yearly"

    class Status(models.TextChoices):
        UPCOMING = "UPCOMING", "Upcoming"
        DUE_TODAY = "DUE_TODAY", "Due today"
        OVERDUE = "OVERDUE", "Overdue"
        PAID = "PAID", "Paid"
        SKIPPED = "SKIPPED", "Skipped"

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="bills")
    title = models.CharField(max_length=120)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="bills"
    )
    payment_method = models.ForeignKey(
        "catalogs.PaymentMethod",
        on_delete=models.PROTECT,
        related_name="bills",
        null=True,
        blank=True,
    )
    member = models.ForeignKey(
        "families.FamilyMember",
        on_delete=models.PROTECT,
        related_name="bills",
        null=True,
        blank=True,
    )
    due_date = models.DateField()
    frequency = models.CharField(max_length=16, default=Frequency.MONTHLY)
    reminder_days = models.PositiveSmallIntegerField(default=3)
    auto_post = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.UPCOMING
    )
    last_paid_on = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["due_date", "title"]
        indexes = [models.Index(fields=["family", "is_active", "due_date"])]

    def __str__(self):
        return self.title
