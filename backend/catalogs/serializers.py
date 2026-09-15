from rest_framework import serializers

from catalogs.models import Category, PaymentMethod, SubCategory
from catalogs.validators import validate_master_code


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = (
            "id",
            "category",
            "name",
            "icon",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        family = self.context["family"]
        category = attrs.get("category") or getattr(self.instance, "category", None)
        if category is None:
            raise serializers.ValidationError({"category": "Category is required."})
        if category.family_id not in (None, family.id):
            raise serializers.ValidationError(
                {"category": "Category does not belong to your family."}
            )
        attrs["family"] = family if category.family_id else None
        if self.instance is None and category.family_id is None:
            attrs["family"] = family
        return attrs


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)
    is_system = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "icon",
            "color",
            "type",
            "is_active",
            "is_system",
            "subcategories",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "is_system", "subcategories")

    def get_is_system(self, obj):
        return obj.family_id is None

    def validate_type(self, value):
        return validate_master_code("transaction_type", value)

    def create(self, validated_data):
        validated_data["family"] = self.context["family"]
        return super().create(validated_data)


class PaymentMethodSerializer(serializers.ModelSerializer):
    is_system = serializers.SerializerMethodField()

    class Meta:
        model = PaymentMethod
        fields = (
            "id",
            "name",
            "icon",
            "is_active",
            "is_system",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "is_system")

    def get_is_system(self, obj):
        return obj.family_id is None

    def create(self, validated_data):
        validated_data["family"] = self.context["family"]
        return super().create(validated_data)
