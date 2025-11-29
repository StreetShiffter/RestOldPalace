from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularSwaggerView

from config import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("restic.urls")),
    path("users/", include("users.urls")),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
