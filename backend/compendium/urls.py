from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("wiki.urls")),
]

# JWT token endpoints. Kept optional so the API also runs with session auth only.
try:  # pragma: no cover - depends on the installed simplejwt build
    from rest_framework_simplejwt import urls as jwt_urls

    urlpatterns.append(path("api/auth/", include(jwt_urls)))
except ImportError:  # pragma: no cover
    pass