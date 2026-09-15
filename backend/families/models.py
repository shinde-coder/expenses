from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel


class Family(TimeStampedUUIDModel):
    name = models.CharField(max_length=120)
    currency = models.CharField(max_length=8, default="INR")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_families",
    )

    class Meta:
        verbose_name_plural = "families"
        ordering = ["name"]

    def __str__(self):
        return self.name


class FamilyMember(TimeStampedUUIDModel):
    class Relationship(models.TextChoices):
        SELF = "SELF", "Me"
        DAD = "DAD", "Dad"
        MOM = "MOM", "Mom"
        SPOUSE = "SPOUSE", "Spouse"
        CHILD = "CHILD", "Child"
        OTHER = "OTHER", "Other"

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        EDITOR = "EDITOR", "Editor"
        VIEWER = "VIEWER", "Viewer"

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memberships",
    )
    display_name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=20, default=Relationship.OTHER)
    avatar = models.ImageField(upload_to="members/", blank=True, null=True)
    role = models.CharField(max_length=16, default=Role.EDITOR)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["family", "user"],
                condition=models.Q(user__isnull=False),
                name="uniq_family_user_membership",
            ),
        ]
        indexes = [
            models.Index(fields=["family", "is_active"]),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.family.name})"


class FamilyInvitation(TimeStampedUUIDModel):
    family = models.ForeignKey(
        Family, on_delete=models.CASCADE, related_name="invitations"
    )
    code = models.CharField(max_length=12, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_invitations",
    )
    expires_at = models.DateTimeField()
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_invitations",
    )
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} → {self.family.name}"
