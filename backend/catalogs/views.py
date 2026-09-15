from django.db.models import ProtectedError, Q
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from catalogs.lookups import masters_payload
from catalogs.models import Category, PaymentMethod, SubCategory
from catalogs.serializers import (
    CategorySerializer,
    PaymentMethodSerializer,
    SubCategorySerializer,
)
from core.mixins import EnvelopeMixin, FamilyContextMixin
from core.responses import success_response


class CatalogViewSet(EnvelopeMixin, FamilyContextMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.user.is_authenticated:
            context["family"] = self.get_family()
        return context

    def _visible(self, model):
        family = self.get_family()
        return model.objects.filter(Q(family__isnull=True) | Q(family=family))

    def _guard_system(self, instance, action="change"):
        if instance.family_id is None:
            raise ValidationError(
                {"detail": f"System records cannot be {action}d. Create a family copy instead."}
            )

    def perform_update(self, serializer):
        self._guard_system(serializer.instance, "update")
        serializer.save()

    def perform_destroy(self, instance):
        self._guard_system(instance, "delete")
        try:
            instance.delete()
        except ProtectedError:
            instance.is_active = False
            instance.save(update_fields=["is_active", "updated_at"])


class CategoryViewSet(CatalogViewSet):
    serializer_class = CategorySerializer
    filterset_fields = ("type", "is_active")
    search_fields = ("name",)

    def get_queryset(self):
        return self._visible(Category).prefetch_related("subcategories")


class SubCategoryViewSet(CatalogViewSet):
    serializer_class = SubCategorySerializer
    filterset_fields = ("category", "is_active")
    search_fields = ("name",)

    def get_queryset(self):
        family = self.get_family()
        return SubCategory.objects.filter(
            Q(family__isnull=True) | Q(family=family) | Q(category__family__isnull=True)
        ).select_related("category")


class PaymentMethodViewSet(CatalogViewSet):
    serializer_class = PaymentMethodSerializer
    filterset_fields = ("is_active",)
    search_fields = ("name",)

    def get_queryset(self):
        return self._visible(PaymentMethod)


class MastersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(masters_payload())
