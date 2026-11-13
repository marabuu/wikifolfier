import logging

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import authenticate
from django.urls import include, path
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from wiki.permissions import user_is_owner

logger = logging.getLogger(__name__)


def _client_ip(request) -> str:
    real_ip = request.META.get("HTTP_X_REAL_IP", "").strip()
    if real_ip:
        return real_ip
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


class OwnerTokenView(APIView):
    """Credential endpoint that refuses every account except OWNER_USERNAME."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        username = request.data.get("username", "")
        user = authenticate(
            request,
            username=username,
            password=request.data.get("password", ""),
        )
        if not user_is_owner(user):
            logger.warning(
                "Failed owner login attempt for username=%r from ip=%s",
                username,
                _client_ip(request),
            )
            return Response({"detail": "Credenciais inválidas."}, status=401)
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token)})


urlpatterns = [
    path(settings.ADMIN_URL_PATH, admin.site.urls),
    path("api/", include("wiki.urls")),
    path("api/auth/owner-token/", OwnerTokenView.as_view(), name="owner-token"),
]

# JWT token endpoints. Kept optional so the API also runs with session auth only.
try:  # pragma: no cover - depends on the installed simplejwt build
    from rest_framework_simplejwt import urls as jwt_urls

    urlpatterns.append(path("api/auth/", include(jwt_urls)))
except ImportError:  # pragma: no cover
    pass
