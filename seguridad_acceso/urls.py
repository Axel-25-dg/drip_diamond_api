from rest_framework.routers import DefaultRouter

from seguridad_acceso.views import IntentoLoginViewSet, IPBloqueadaViewSet, LogAuditoriaViewSet

router = DefaultRouter()
router.register('intentos-login', IntentoLoginViewSet, basename='intento-login')
router.register('ips-bloqueadas', IPBloqueadaViewSet, basename='ip-bloqueada')
router.register('auditoria', LogAuditoriaViewSet, basename='auditoria')

urlpatterns = router.urls
