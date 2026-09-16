from django.contrib import admin

from ledger.models import FinancialTransaction


@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "occurred_on",
        "type",
        "amount",
        "category_name_snapshot",
        "member",
        "family",
        "is_deleted",
    )
    list_filter = ("type", "is_deleted", "occurred_on", "payment_method")
    search_fields = (
        "description",
        "notes",
        "category_name_snapshot",
        "family__name",
    )
    autocomplete_fields = (
        "family",
        "created_by",
        "category",
        "subcategory",
        "payment_method",
        "member",
    )
    date_hierarchy = "occurred_on"
