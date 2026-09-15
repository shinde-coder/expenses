from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.mixins import EnvelopeMixin, FamilyContextMixin
from core.responses import error_response, success_response
from families.invitations import accept_invitation, create_invitation
from families.models import FamilyInvitation, FamilyMember
from families.serializers import (
    FamilyInvitationSerializer,
    FamilyMemberSerializer,
    FamilySerializer,
)
from ledger.models import FinancialTransaction
from ledger.serializers import TransactionSerializer


class CurrentFamilyView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(FamilySerializer(self.get_family()).data)

    def patch(self, request):
        serializer = FamilySerializer(
            self.get_family(), data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(serializer.data, "Family updated.")


class FamilyMemberViewSet(
    EnvelopeMixin,
    FamilyContextMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = FamilyMemberSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return FamilyMember.objects.filter(family=self.get_family())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            context["family"] = self.get_family()
        return context

    def perform_destroy(self, instance):
        if instance.user_id == self.request.user.id:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"detail": "You cannot remove your own membership."})
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class FamilyInvitationCreateView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = FamilyInvitation.objects.filter(
            family=self.get_family(), accepted_at__isnull=True
        )
        return success_response(FamilyInvitationSerializer(items, many=True).data)

    def post(self, request):
        invite = create_invitation(self.get_family(), request.user)
        return success_response(
            FamilyInvitationSerializer(invite).data,
            "Invite code created.",
            status=201,
        )


class FamilyInvitationAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = (request.data.get("code") or "").strip()
        if not code:
            return error_response("Invite code is required.", status=400)
        try:
            invite, member = accept_invitation(request.user, code)
        except ValueError as exc:
            return error_response(str(exc), status=400)
        return success_response(
            {
                "family": FamilySerializer(invite.family).data,
                "member": FamilyMemberSerializer(member).data,
            },
            "Joined family.",
        )


class FamilyActivityView(FamilyContextMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = (
            FinancialTransaction.objects.filter(
                family=self.get_family(), is_deleted=False
            )
            .select_related("category", "member", "payment_method")
            .order_by("-occurred_on", "-created_at")[:30]
        )
        return success_response(TransactionSerializer(items, many=True).data)
