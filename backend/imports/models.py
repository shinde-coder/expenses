from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel
from families.models import Family


class ImportBatch(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        COMPLETED = "COMPLETED"
        FAILED = "FAILED"

    family = models.ForeignKey(
        Family, on_delete=models.CASCADE, related_name="import_batches"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="import_batches",
    )
    filename = models.CharField(max_length=255)
    dry_run = models.BooleanField(default=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    success_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)
    summary = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]


class ImportRowError(TimeStampedUUIDModel):
    batch = models.ForeignKey(
        ImportBatch, on_delete=models.CASCADE, related_name="row_errors"
    )
    row_number = models.PositiveIntegerField()
    code = models.CharField(max_length=40)
    reason = models.CharField(max_length=255)
    raw = models.JSONField(default=dict, blank=True)
