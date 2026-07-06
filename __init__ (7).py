from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include


def health_check(request):
    """Railway / Render ping this URL to confirm the server is alive.
    Returns 200 immediately — no database query, no auth, nothing that
    can fail. If this endpoint 200s, the server is running."""
    return JsonResponse({"status": "ok", "service": "lamlibaas-api"})


urlpatterns = [
    path("health/", health_check),
    path("admin/", admin.site.urls),
    path("api/v1/", include("shop.urls")),
    path("api/v1/orders/", include("orders.urls")),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/payments/", include("payments.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
