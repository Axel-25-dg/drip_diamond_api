from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

from tienda.views.auth_views import (
    ConfirmarRecuperacionView,
    LoginView,
    LogoutView,
    SolicitarRecuperacionView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/recuperar-password/', SolicitarRecuperacionView.as_view(), name='recuperar-password'),
    path('api/auth/confirmar-password/', ConfirmarRecuperacionView.as_view(), name='confirmar-password'),

    path('api/', include('tienda.urls')),
    path('api/seguridad/', include('seguridad_acceso.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
