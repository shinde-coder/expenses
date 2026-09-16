from rest_framework import serializers

from catalogs.validators import validate_master_code
from ledger.models import FinancialTransaction


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category_name_snapshot", read_only=True)
    subcategory_name = serializers.CharField(
        source="subcategory_name_snapshot", read_only=True
    )
    payment_method_name = serializers.CharField(
        source="payment_method.name", read_only=True
    )
    payment_method_icon = serializers.CharField(
        source="payment_method.icon", read_only=True
    )
    member_name = serializers.CharField(source="member.display_name", read_only=True)
    category_icon = serializers.CharField(source="category.icon", read_only=True)
    category_color = serializers.CharField(source="category.color", read_only=True)

    class Meta:
        model = FinancialTransaction
        fields = (
            "id",
            "type",
            "amount",
            "occurred_on",
            "category",
            "category_name",
            "category_icon",
            "category_color",
            "subcategory",
            "subcategory_name",
            "payment_method",
            "payment_method_name",
            "payment_method_icon",
            "member",
            "member_name",
            "description",
            "notes",
            "tags",
            "recurring_expense",
            "client_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "category_name",
            "category_icon",
            "category_color",
            "subcategory_name",
            "payment_method_name",
            "payment_method_icon",
            "member_name",
            "recurring_expense",
            "created_at",
            "updated_at",
        )

    def validate_tags(self, value):
        if value in (None, ""):
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list of strings.")
        cleaned = []
        for item in value:
            tag = str(item).strip().lstrip("#")
            if tag:
                cleaned.append(tag[:40])
        return cleaned[:12]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_type(self, value):
        return validate_master_code("transaction_type", value)

    def _belongs(self, obj, family, label):
        if obj is None:
            return
        family_id = getattr(obj, "family_id", None)
        if family_id not in (None, family.id):
            raise serializers.ValidationError({label: f"{label} does not belong to your family."})

    def validate(self, attrs):
        family = self.context["family"]
        instance = self.instance
        txn_type = attrs.get("type") or getattr(instance, "type", None)
        category = attrs.get("category") or getattr(instance, "category", None)
        subcategory = attrs.get("subcategory", getattr(instance, "subcategory", None))
        if "subcategory" in attrs:
            subcategory = attrs.get("subcategory")
        payment_method = attrs.get("payment_method") or getattr(
            instance, "payment_method", None
        )
        member = attrs.get("member") or getattr(instance, "member", None)

        if category is None:
            raise serializers.ValidationError({"category": "Category is required."})
        if payment_method is None:
            raise serializers.ValidationError(
                {"payment_method": "Payment method is required."}
            )
        if member is None:
            raise serializers.ValidationError({"member": "Family member is required."})

        self._belongs(category, family, "category")
        self._belongs(payment_method, family, "payment_method")
        if member.family_id != family.id or not member.is_active:
            raise serializers.ValidationError(
                {"member": "Paid by / received by must be an active family member."}
            )
        if not category.is_active:
            raise serializers.ValidationError({"category": "Category is inactive."})
        if category.type != txn_type:
            raise serializers.ValidationError(
                {"category": "Category type must match the transaction type."}
            )
        if subcategory is not None:
            if subcategory.category_id != category.id:
                raise serializers.ValidationError(
                    {"subcategory": "Subcategory must belong to the selected category."}
                )
            if subcategory.family_id not in (None, family.id):
                raise serializers.ValidationError(
                    {"subcategory": "Subcategory does not belong to your family."}
                )
            if not subcategory.is_active:
                raise serializers.ValidationError(
                    {"subcategory": "Subcategory is inactive."}
                )
        return attrs

    def create(self, validated_data):
        validated_data["family"] = self.context["family"]
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
