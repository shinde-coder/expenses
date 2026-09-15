from django.contrib import admin

from imports.models import ImportBatch, ImportRowError


class ImportRowErrorInline(admin.TabularInline):
    model = ImportRowError
    extra = 0


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = (
        "filename",
        "family",
        "dry_run",
        "status",
        "success_count",
        "failed_count",
        "duplicate_count",
    )
    list_filter = ("status", "dry_run")
    search_fields = ("filename", "family__name")
    inlines = (ImportRowErrorInline,)


@admin.register(ImportRowError)
class ImportRowErrorAdmin(admin.ModelAdmin):
    list_display = ("batch", "row_number", "code", "reason")
    list_filter = ("code",)
    search_fields = ("reason",)
