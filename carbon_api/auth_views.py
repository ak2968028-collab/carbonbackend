from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AdminUser


def user_payload(user):
    return {
        "id": user.pk,
        "username": user.username,
        "email": user.email,
        "is_staff": user.is_staff,
    }


def token_user_for_admin(admin_user):
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username=admin_user.username,
        defaults={
            "email": admin_user.email,
            "is_staff": True,
            "is_superuser": False,
            "is_active": admin_user.is_active,
        },
    )
    changed = False
    for field, value in {
        "email": admin_user.email,
        "password": admin_user.password,
        "is_staff": True,
        "is_active": admin_user.is_active,
    }.items():
        if getattr(user, field) != value:
            setattr(user, field, value)
            changed = True
    if changed:
        user.save(update_fields=["email", "password", "is_staff", "is_active"])
    return user


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = str(request.data.get("username", "")).strip()
        password = str(request.data.get("password", "")).strip()
        if not username or not password:
            return Response(
                {"error": "username and password required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            admin_user = AdminUser.objects.get(username=username)
        except AdminUser.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not admin_user.check_password(password):
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not admin_user.is_active:
            return Response(
                {"error": "Admin user is inactive"},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = token_user_for_admin(admin_user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": user_payload(user)})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({"message": "Logged out"})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(user_payload(request.user))
