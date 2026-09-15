from django.urls import include, path
from rest_framework.routers import DefaultRouter

from catalogs.views import (
    CategoryViewSet,
    MastersView,
    PaymentMethodViewSet,
    SubCategoryViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="categories")
router.register("subcategories", SubCategoryViewSet, basename="subcategories")
router.register("payment-methods", PaymentMethodViewSet, basename="payment-methods")

urlpatterns = [
    path("masters/", MastersView.as_view(), name="masters"),
    path("", include(router.urls)),
]
