import secrets
from datetime import timedelta

from django.utils import timezone

from families.models import FamilyInvitation, FamilyMember


def _code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(8))


def create_invitation(family, user, days=14):
    code = _code()
    while FamilyInvitation.objects.filter(code=code).exists():
        code = _code()
    return FamilyInvitation.objects.create(
        family=family,
        code=code,
        created_by=user,
        expires_at=timezone.now() + timedelta(days=days),
    )


def accept_invitation(user, code):
    invite = FamilyInvitation.objects.select_related("family").filter(code=code.upper()).first()
    if invite is None:
        raise ValueError("Invite code not found.")
    if invite.accepted_at is not None:
        raise ValueError("This invite has already been used.")
    if invite.expires_at < timezone.now():
        raise ValueError("This invite has expired.")
    if FamilyMember.objects.filter(family=invite.family, user=user, is_active=True).exists():
        raise ValueError("You already belong to this family.")

    FamilyMember.objects.filter(user=user, is_active=True).update(is_active=False)
    member = FamilyMember.objects.create(
        family=invite.family,
        user=user,
        display_name=user.name,
        relationship=FamilyMember.Relationship.OTHER,
        role=FamilyMember.Role.EDITOR,
    )
    invite.accepted_by = user
    invite.accepted_at = timezone.now()
    invite.save(update_fields=["accepted_by", "accepted_at", "updated_at"])
    return invite, member
