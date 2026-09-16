from rest_framework import serializers

from notifications.models import AppNotification


class AppNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppNotification
        fields = (
            "id",
            "type",
            "title",
            "body",
            "payload",
            "read_at",
            "sent_at",
            "created_at",
        )
        read_only_fields = fields
