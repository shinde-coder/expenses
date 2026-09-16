from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from catalogs.models import Category, PaymentMethod, SubCategory
from core.models import TimeStampedUUIDModel
from families.models import Family, FamilyMember


class FinancialTransaction(TimeStampedUUIDModel):
    family = models.ForeignKey(
        Family, on_delete=models.CASCADE, related_name="transactions"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_transactions",
    )
    type = models.CharField(max_length=16)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    occurred_on = models.DateField()
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="transactions"
    )
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="transactions",
    )
    payment_method = models.ForeignKey(
        PaymentMethod, on_delete=models.PROTECT, related_name="transactions"
    )
    member = models.ForeignKey(
        FamilyMember,
        on_delete=models.PROTECT,
        related_name="transactions",
        help_text="Paid by (expense/saving) or received by (income).",
    )
    description = models.CharField(max_length=255, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    tags = models.JSONField(default=list, blank=True)
    client_id = models.UUIDField(null=True, blank=True)
    recurring_expense = models.ForeignKey(
        "planning.RecurringExpense",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_transactions",
    )
    is_deleted = models.BooleanField(default=False)
    category_name_snapshot = models.CharField(max_length=80)
    subcategory_name_snapshot = models.CharField(max_length=80, blank=True, default="")

    class Meta:
        ordering = ["-occurred_on", "-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0),
                name="txn_amount_gt_zero",
            ),
            models.UniqueConstraint(
                fields=["family", "client_id"],
                condition=models.Q(client_id__isnull=False),
                name="uniq_family_client_id",
            ),
        ]
        indexes = [
            models.Index(fields=["family", "occurred_on"]),
            models.Index(fields=["family", "type", "occurred_on"]),
            models.Index(fields=["family", "category"]),
            models.Index(fields=["family", "member"]),
            models.Index(fields=["family", "payment_method"]),
            models.Index(fields=["family", "is_deleted", "occurred_on"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.type} {self.amount} {self.occurred_on}"

    def save(self, *args, **kwargs):
        if self.category_id:
            self.category_name_snapshot = self.category.name
        if self.subcategory_id:
            self.subcategory_name_snapshot = self.subcategory.name
        else:
            self.subcategory_name_snapshot = ""
        super().save(*args, **kwargs)
