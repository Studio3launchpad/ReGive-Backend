from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic import TemplateView

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # API routes
    path("api/", include("api.urls")),

    # dj-rest-auth login, logout, password reset
    path("api/auth/", include("dj_rest_auth.urls")),

    # dj-rest-auth registration (uses your custom serializer)
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),

    # API schema + docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    path(
        "",
        TemplateView.as_view(
            template_name="home.html",
            extra_context={"year": 2025}
        ),
        name="home",
    ),
]

# serve media
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
