from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenRefreshView

from tienda.views.auth_views import (
    ConfirmarRecuperacionView,
    LoginView,
    LogoutView,
    SolicitarRecuperacionView,
    VerificarOTPView,
)

from django.http import JsonResponse
from django.views.generic import TemplateView

def root_api_view(request):
    return JsonResponse({
        "status": "online",
        "name": "Drip Diamond API",
        "version": "1.0.0",
        "docs": "/api/docs/"
    })

from tienda.views.media_views import servir_archivo_db

urlpatterns = [
    path('', root_api_view, name='api-root-index'),
    path('admin/push-studio/', TemplateView.as_view(template_name='admin/push_studio.html'), name='admin-push-studio'),
    path('admin/', admin.site.urls),

    # Servir archivos y fotos desde la Base de Datos (compatible con Vercel)
    path('api/media/<path:ruta>', servir_archivo_db, name='servir-media-api'),
    path('media/<path:ruta>', servir_archivo_db, name='servir-media'),

    # Documentación Swagger / OpenAPI / Redoc
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Autenticación JWT & OTP Password Recovery
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/recuperar-password/', SolicitarRecuperacionView.as_view(), name='recuperar-password'),
    path('api/auth/verificar-otp/', VerificarOTPView.as_view(), name='verificar-otp'),
    path('api/auth/confirmar-password/', ConfirmarRecuperacionView.as_view(), name='confirmar-password'),

    path('api/', include('tienda.urls')),
    path('api/seguridad/', include('seguridad_acceso.urls')),
]
