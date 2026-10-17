import os

from rest_framework.permissions import SAFE_METHODS, BasePermission


def user_is_owner(user) -> bool:
    """Only the explicitly configured owner may make changes.

    An unset OWNER_USERNAME intentionally grants nobody write access.
    """
    owner_username = os.environ.get("OWNER_USERNAME", "").strip()
    return bool(
        owner_username
        and user
        and user.is_authenticated
        and user.is_superuser
        and user.username == owner_username
    )


class IsViewerOrReadOnly(BasePermission):
    """Anyone may read public content; editors/admins may write."""

    message = "É necessário ter permissão de editor (staff) para modificar o compêndio."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return user_is_owner(user)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return user_is_owner(request.user)


class IsGMOrReadOnly(IsViewerOrReadOnly):
    """Also allows access to gm_only pages."""

    message = "Conteúdo restrito ao GM."

    def has_permission(self, request, view):
        return super().has_permission(request, view)


def user_is_gm(user) -> bool:
    return bool(user and user.is_authenticated and user.is_staff)
