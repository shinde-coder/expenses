from rest_framework import serializers

from catalogs.validators import validate_master_code
from families.models import Family, FamilyInvitation, FamilyMember


class FamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = Family
        fields = ("id", "name", "currency", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class FamilyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMember
        fields = (
            "id",
            "display_name",
            "relationship",
            "avatar",
            "user",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "created_at", "updated_at")

    def validate_display_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError("Name is required.")
        return name

    def validate_relationship(self, value):
        return validate_master_code("relationship", value)

    def validate_role(self, value):
        return validate_master_code("member_role", value)

    def create(self, validated_data):
        validated_data["family"] = self.context["family"]
        return super().create(validated_data)


class FamilyInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyInvitation
        fields = (
            "id",
            "code",
            "expires_at",
            "accepted_at",
            "created_at",
        )
        read_only_fields = fields
