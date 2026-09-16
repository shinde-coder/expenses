from calendar import monthrange
from datetime import date

from django_filters import rest_framework as filters

from ledger.models import FinancialTransaction


class TransactionFilter(filters.FilterSet):
    type = filters.CharFilter(field_name="type")
    date_from = filters.DateFilter(field_name="occurred_on", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="occurred_on", lookup_expr="lte")
    month = filters.CharFilter(method="filter_month")
    category = filters.UUIDFilter(field_name="category_id")
    subcategory = filters.UUIDFilter(field_name="subcategory_id")
    payment_method = filters.UUIDFilter(field_name="payment_method_id")
    member = filters.UUIDFilter(field_name="member_id")
    amount_min = filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max = filters.NumberFilter(field_name="amount", lookup_expr="lte")
    tag = filters.CharFilter(method="filter_tag")

    class Meta:
        model = FinancialTransaction
        fields = (
            "type",
            "date_from",
            "date_to",
            "month",
            "category",
            "subcategory",
            "payment_method",
            "member",
            "amount_min",
            "amount_max",
            "tag",
        )

    def filter_tag(self, queryset, name, value):
        tag = (value or "").strip().lstrip("#")
        if not tag:
            return queryset
        return queryset.filter(tags__contains=[tag])

    def filter_month(self, queryset, name, value):
        try:
            year, month = value.split("-")
            year, month = int(year), int(month)
            start = date(year, month, 1)
            end = date(year, month, monthrange(year, month)[1])
        except (ValueError, TypeError):
            return queryset.none()
        return queryset.filter(occurred_on__gte=start, occurred_on__lte=end)
