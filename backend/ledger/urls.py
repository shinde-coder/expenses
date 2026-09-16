from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ledger.views import TransactionViewSet

router = DefaultRouter()
router.register("transactions", TransactionViewSet, basename="transactions")

urlpatterns = [path("", include(router.urls))]
