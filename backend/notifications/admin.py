from django.contrib import admin

from notifications.models import AppNotification


@admin.register(AppNotification)
class AppNotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "family", "read_at", "created_at")
    list_filter = ("type",)
    search_fields = ("title", "body", "family__name")
