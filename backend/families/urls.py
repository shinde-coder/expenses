from django.urls import include, path
from rest_framework.routers import DefaultRouter

from families.views import (
    CurrentFamilyView,
    FamilyActivityView,
    FamilyInvitationAcceptView,
    FamilyInvitationCreateView,
    FamilyMemberViewSet,
)

router = DefaultRouter()
router.register("members", FamilyMemberViewSet, basename="members")

urlpatterns = [
    path("families/current/", CurrentFamilyView.as_view(), name="family-current"),
    path("families/invitations/", FamilyInvitationCreateView.as_view(), name="family-invites"),
    path(
        "families/invitations/accept/",
        FamilyInvitationAcceptView.as_view(),
        name="family-invite-accept",
    ),
    path("families/activity/", FamilyActivityView.as_view(), name="family-activity"),
    path("", include(router.urls)),
]
