from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel
from families.models import Family


class AppNotification(TimeStampedUUIDModel):
    class Type(models.TextChoices):
        BUDGET_NEAR = "BUDGET_NEAR", "Budget near limit"
        BUDGET_EXCEEDED = "BUDGET_EXCEEDED", "Budget exceeded"
        RECURRING_DUE = "RECURRING_DUE", "Recurring expense due"
        MONTHLY_SUMMARY = "MONTHLY_SUMMARY", "Monthly summary"
        GOAL_REMINDER = "GOAL_REMINDER", "Savings goal reminder"

    family = models.ForeignKey(
        Family, on_delete=models.CASCADE, related_name="notifications"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    type = models.CharField(max_length=32, choices=Type.choices)
    title = models.CharField(max_length=160)
    body = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    dedupe_key = models.CharField(max_length=160, blank=True, default="")
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["family", "read_at"]),
            models.Index(fields=["family", "dedupe_key"]),
        ]

    def __str__(self):
        return self.title
