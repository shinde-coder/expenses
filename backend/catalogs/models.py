from django.db import models

from core.models import TimeStampedUUIDModel
from families.models import Family


class CategoryType(models.TextChoices):
    EXPENSE = "EXPENSE", "Expense"
    INCOME = "INCOME", "Income"
    SAVING = "SAVING", "Saving"


class Category(TimeStampedUUIDModel):
    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="categories",
    )
    name = models.CharField(max_length=80)
    icon = models.CharField(max_length=64, default="category")
    color = models.CharField(max_length=16, default="#5B8DEF")
    type = models.CharField(max_length=16)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["type", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "type"],
                condition=models.Q(family__isnull=True),
                name="uniq_system_category_name_type",
            ),
            models.UniqueConstraint(
                fields=["family", "name", "type"],
                condition=models.Q(family__isnull=False),
                name="uniq_family_category_name_type",
            ),
        ]
        indexes = [
            models.Index(fields=["family", "type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.type})"


class SubCategory(TimeStampedUUIDModel):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="subcategories"
    )
    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
    )
    name = models.CharField(max_length=80)
    icon = models.CharField(max_length=64, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"],
                name="uniq_subcategory_name_per_category",
            ),
        ]
        indexes = [
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self):
        return f"{self.category.name} / {self.name}"


class PaymentMethod(TimeStampedUUIDModel):
    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="payment_methods",
    )
    name = models.CharField(max_length=80)
    icon = models.CharField(max_length=64, default="payments")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name"],
                condition=models.Q(family__isnull=True),
                name="uniq_system_payment_method_name",
            ),
            models.UniqueConstraint(
                fields=["family", "name"],
                condition=models.Q(family__isnull=False),
                name="uniq_family_payment_method_name",
            ),
        ]

    def __str__(self):
        return self.name


class MasterValue(TimeStampedUUIDModel):
    """Lookup rows served to the app: types, relationships, frequencies, reports, etc."""

    group = models.CharField(max_length=40)
    code = models.CharField(max_length=40)
    label = models.CharField(max_length=80)
    icon = models.CharField(max_length=64, blank=True, default="")
    color = models.CharField(max_length=16, blank=True, default="")
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["group", "sort_order", "label"]
        constraints = [
            models.UniqueConstraint(fields=["group", "code"], name="uniq_master_group_code"),
        ]
        indexes = [
            models.Index(fields=["group", "is_active", "sort_order"]),
        ]

    def __str__(self):
        return f"{self.group}:{self.code}"
