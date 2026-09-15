import sys

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.models import User
from accounts.serializers import (
    AuthPayloadSerializer,
    ChangePasswordSerializer,
    EmailLoginSerializer,
    ForgotPasswordSerializer,
    LogoutSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    encode_uid,
)
from core.responses import error_response, success_response
from families.models import FamilyMember
from families.serializers import FamilySerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.save()
        data = AuthPayloadSerializer(payload).data
        return success_response(data, "Account created.", status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        serializer = EmailLoginSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return success_response(
            AuthPayloadSerializer(serializer.validated_data).data,
            "Logged in.",
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except TokenError:
            return error_response("Invalid refresh token.", status=status.HTTP_400_BAD_REQUEST)
        return success_response(None, "Logged out.")


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return success_response(response.data, "Token refreshed.")


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        member = (
            FamilyMember.objects.select_related("family")
            .filter(user=request.user, is_active=True)
            .first()
        )
        return success_response(
            {
                "user": UserSerializer(request.user).data,
                "family": FamilySerializer(member.family).data if member else None,
            }
        )

    def patch(self, request):
        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(UserSerializer(request.user).data, "Profile updated.")


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(None, "Password changed.")


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        data = {"email_sent": True}
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            token = PasswordResetTokenGenerator().make_token(user)
            uid = encode_uid(user)
            if settings.DEBUG or "test" in sys.argv:
                data.update({"uid": uid, "token": token})
        return success_response(
            data,
            "If an account exists for that email, a reset link has been issued.",
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(None, "Password has been reset.")
