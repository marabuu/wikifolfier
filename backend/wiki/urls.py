from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("pages", views.PageViewSet, basename="page")
router.register("categories", views.CategoryViewSet, basename="category")
router.register("tags", views.TagViewSet, basename="tag")
router.register("broken-links", views.BrokenLinkViewSet, basename="brokenlink")

urlpatterns = [
    path("search", views.SearchView.as_view(), name="search"),
    path("spells-index", views.SpellIndexView.as_view(), name="spells-index"),
    path("navigation", views.NavigationView.as_view(), name="navigation"),
    path("health", views.HealthView.as_view(), name="health"),
    path("", include(router.urls)),
]