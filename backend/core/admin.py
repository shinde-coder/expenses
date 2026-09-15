from django.contrib import admin

from core.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "model", "family", "actor")
    list_filter = ("action", "model")
    search_fields = ("object_id", "family__name", "actor__email")
    readonly_fields = (
        "actor",
        "family",
        "action",
        "model",
        "object_id",
        "before",
        "after",
        "created_at",
        "updated_at",
    )
