from rest_framework import serializers

from catalogs.lookups import is_valid_master


def validate_master_code(group, value):
    if value in (None, ""):
        return value
    if not is_valid_master(group, value):
        raise serializers.ValidationError(
            f"Unknown {group.replace('_', ' ')}."
        )
    return value
