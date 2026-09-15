from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

admin.site.site_header = "Family Expenses Admin"
admin.site.site_title = "Family Expenses"
admin.site.index_title = "Internal administration"

urlpatterns = [
    path("health/", lambda request: JsonResponse({"ok": True})),
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/", include("families.urls")),
    path("api/v1/", include("catalogs.urls")),
    path("api/v1/", include("ledger.urls")),
    path("api/v1/", include("planning.urls")),
    path("api/v1/", include("insights.urls")),
    path("api/v1/", include("notifications.urls")),
    path("api/v1/", include("imports.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
