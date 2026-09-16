from decimal import Decimal

from rest_framework import serializers

from catalogs.models import Category
from catalogs.validators import validate_master_code
from planning.models import Bill, FinancialGoal, RecurringExpense


class CategoryBudgetItemSerializer(serializers.Serializer):
    category = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0")
    )


class BudgetUpsertSerializer(serializers.Serializer):
    month = serializers.RegexField(r"^\d{4}-\d{2}$")
    overall_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0"), required=False, allow_null=True
    )
    items = CategoryBudgetItemSerializer(many=True, required=False)

    def validate_items(self, items):
        family = self.context["family"]
        ids = [item["category"] for item in items]
        found = {
            str(pk): obj
            for pk, obj in Category.objects.filter(id__in=ids).in_bulk().items()
        }
        for item in items:
            category = found.get(str(item["category"]))
            if category is None:
                raise serializers.ValidationError("Unknown category.")
            if category.family_id not in (None, family.id):
                raise serializers.ValidationError(
                    "Category does not belong to your family."
                )
            item["category_obj"] = category
        return items


class CopyBudgetSerializer(serializers.Serializer):
    month = serializers.RegexField(r"^\d{4}-\d{2}$")


class RecurringExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_icon = serializers.CharField(source="category.icon", read_only=True)
    category_color = serializers.CharField(source="category.color", read_only=True)
    payment_method_icon = serializers.CharField(
        source="payment_method.icon", read_only=True
    )

    class Meta:
        model = RecurringExpense
        fields = (
            "id",
            "title",
            "amount",
            "category",
            "category_name",
            "category_icon",
            "category_color",
            "subcategory",
            "payment_method",
            "payment_method_icon",
            "member",
            "frequency",
            "start_date",
            "end_date",
            "next_due_date",
            "is_active",
            "auto_create",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "category_name",
            "category_icon",
            "category_color",
            "payment_method_icon",
            "created_at",
            "updated_at",
        )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_frequency(self, value):
        return validate_master_code("frequency", value)

    def validate(self, attrs):
        family = self.context["family"]
        instance = self.instance
        category = attrs.get("category") or getattr(instance, "category", None)
        subcategory = attrs.get("subcategory", getattr(instance, "subcategory", None))
        if "subcategory" in attrs:
            subcategory = attrs.get("subcategory")
        member = attrs.get("member") or getattr(instance, "member", None)
        method = attrs.get("payment_method") or getattr(instance, "payment_method", None)
        if category and category.family_id not in (None, family.id):
            raise serializers.ValidationError({"category": "Invalid category."})
        if method and method.family_id not in (None, family.id):
            raise serializers.ValidationError({"payment_method": "Invalid payment method."})
        if member and member.family_id != family.id:
            raise serializers.ValidationError({"member": "Member must belong to your family."})
        if subcategory is not None and category and subcategory.category_id != category.id:
            raise serializers.ValidationError(
                {"subcategory": "Subcategory must belong to the selected category."}
            )
        start = attrs.get("start_date") or getattr(instance, "start_date", None)
        if not attrs.get("next_due_date") and start:
            attrs["next_due_date"] = start
        return attrs

    def create(self, validated_data):
        validated_data["family"] = self.context["family"]
        return super().create(validated_data)


class FinancialGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialGoal
        fields = (
            "id",
            "name",
            "target_amount",
            "current_amount",
            "target_date",
            "description",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_status(self, value):
        return validate_master_code("goal_status", value)

    def create(self, validated_data):
        validated_data["family"] = self.context["family"]
        return super().create(validated_data)


class GoalContributeSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    note = serializers.CharField(required=False, allow_blank=True, default="")
    withdraw = serializers.BooleanField(required=False, default=False)


class BillSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_icon = serializers.CharField(source="category.icon", read_only=True)
    category_color = serializers.CharField(source="category.color", read_only=True)

    class Meta:
        model = Bill
        fields = (
            "id",
            "title",
            "amount",
            "category",
            "category_name",
            "category_icon",
            "category_color",
            "payment_method",
            "member",
            "due_date",
            "frequency",
            "reminder_days",
            "auto_post",
            "is_active",
            "last_status",
            "last_paid_on",
            "notes",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "category_name",
            "category_icon",
            "category_color",
            "last_status",
            "last_paid_on",
            "status",
            "created_at",
            "updated_at",
        )

    def get_status(self, obj):
        from planning.bills import computed_status

        return computed_status(obj)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_frequency(self, value):
        return validate_master_code("frequency", value)

    def validate(self, attrs):
        family = self.context["family"]
        instance = self.instance
        category = attrs.get("category") or getattr(instance, "category", None)
        method = attrs.get("payment_method", getattr(instance, "payment_method", None))
        member = attrs.get("member", getattr(instance, "member", None))
        if category and category.family_id not in (None, family.id):
            raise serializers.ValidationError({"category": "Invalid category."})
        if method and method.family_id not in (None, family.id):
            raise serializers.ValidationError({"payment_method": "Invalid payment method."})
        if member and member.family_id != family.id:
            raise serializers.ValidationError({"member": "Member must belong to your family."})
        return attrs

    def create(self, validated_data):
        validated_data["family"] = self.context["family"]
        return super().create(validated_data)
