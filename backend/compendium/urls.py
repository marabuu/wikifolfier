from django.contrib import admin
from django.contrib.auth import authenticate
from django.urls import include, path
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from wiki.permissions import user_is_owner


class OwnerTokenView(APIView):
    """Credential endpoint that refuses every account except OWNER_USERNAME."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        user = authenticate(
            request,
            username=request.data.get("username", ""),
            password=request.data.get("password", ""),
        )
        if not user_is_owner(user):
            return Response({"detail": "Credenciais inválidas."}, status=401)
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token)})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("wiki.urls")),
    path("api/auth/owner-token/", OwnerTokenView.as_view(), name="owner-token"),
]

# JWT token endpoints. Kept optional so the API also runs with session auth only.
try:  # pragma: no cover - depends on the installed simplejwt build
    from rest_framework_simplejwt import urls as jwt_urls

    urlpatterns.append(path("api/auth/", include(jwt_urls)))
except ImportError:  # pragma: no cover
    pass
