from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from core.audit import write_audit
from core.mixins import EnvelopeMixin, FamilyContextMixin
from core.pagination import EnvelopePagination
from core.responses import success_response
from ledger.filters import TransactionFilter
from ledger.models import FinancialTransaction
from ledger.serializers import TransactionSerializer


class TransactionViewSet(EnvelopeMixin, FamilyContextMixin, viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = EnvelopePagination
    filterset_class = TransactionFilter
    search_fields = ("description", "notes", "category_name_snapshot", "subcategory_name_snapshot")
    ordering_fields = ("occurred_on", "amount", "created_at")
    ordering = ("-occurred_on", "-created_at")

    def get_queryset(self):
        return (
            FinancialTransaction.objects.filter(
                family=self.get_family(), is_deleted=False
            )
            .select_related("category", "subcategory", "payment_method", "member")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            context["family"] = self.get_family()
        return context

    def perform_create(self, serializer):
        instance = serializer.save()
        write_audit(
            actor=self.request.user,
            family=instance.family,
            action="create",
            instance=instance,
            after={"amount": str(instance.amount), "type": instance.type},
        )

    def perform_update(self, serializer):
        before = {"amount": str(serializer.instance.amount)}
        instance = serializer.save()
        write_audit(
            actor=self.request.user,
            family=instance.family,
            action="update",
            instance=instance,
            before=before,
            after={"amount": str(instance.amount)},
        )

    def perform_destroy(self, instance):
        write_audit(
            actor=self.request.user,
            family=instance.family,
            action="delete",
            instance=instance,
            before={"amount": str(instance.amount), "occurred_on": str(instance.occurred_on)},
        )
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted", "updated_at"])

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk=None):
        source = self.get_object()
        clone = FinancialTransaction.objects.create(
            family=source.family,
            created_by=request.user,
            type=source.type,
            amount=source.amount,
            occurred_on=source.occurred_on,
            category=source.category,
            subcategory=source.subcategory,
            payment_method=source.payment_method,
            member=source.member,
            description=source.description,
            notes=source.notes,
            tags=list(source.tags or []),
        )
        write_audit(
            actor=request.user,
            family=clone.family,
            action="create",
            instance=clone,
            after={"amount": str(clone.amount), "type": clone.type, "duplicated_from": str(source.id)},
        )
        return success_response(
            TransactionSerializer(clone).data,
            "Transaction duplicated.",
            status=201,
        )
