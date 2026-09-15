from rest_framework.exceptions import PermissionDenied

from families.models import FamilyMember


def get_user_family(user):
    member = (
        FamilyMember.objects.select_related("family")
        .filter(user=user, is_active=True)
        .first()
    )
    if member is None:
        raise PermissionDenied("You do not belong to an active family.")
    return member.family, member
