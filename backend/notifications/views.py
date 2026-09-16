from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from core.mixins import EnvelopeMixin, FamilyContextMixin
from core.pagination import EnvelopePagination
from core.responses import success_response
from notifications.models import AppNotification
from notifications.serializers import AppNotificationSerializer
from notifications.services import generate_family_notifications


class NotificationViewSet(
    EnvelopeMixin,
    FamilyContextMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AppNotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = EnvelopePagination

    def get_queryset(self):
        return AppNotification.objects.filter(family=self.get_family())

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        note = self.get_object()
        if note.read_at is None:
            note.read_at = timezone.now()
            note.save(update_fields=["read_at", "updated_at"])
        return success_response(AppNotificationSerializer(note).data, "Marked as read.")

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset().filter(read_at__isnull=True).count()
        return success_response({"unread": count})

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        updated = self.get_queryset().filter(read_at__isnull=True).update(
            read_at=timezone.now()
        )
        return success_response({"updated": updated}, "All notifications marked as read.")

    @action(detail=False, methods=["post"])
    def generate(self, request):
        created = generate_family_notifications(
            self.get_family(), month=request.data.get("month")
        )
        return success_response(
            AppNotificationSerializer(created, many=True).data,
            f"Generated {len(created)} notification(s).",
        )
