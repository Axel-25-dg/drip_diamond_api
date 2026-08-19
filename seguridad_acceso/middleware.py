from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


def _obtener_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class ControlAccesoMiddleware(MiddlewareMixin):
    """Corta la petición si la IP está bloqueada por intentos fallidos de login."""

    RUTAS_EXENTAS = ('/admin/',)

    def process_request(self, request):
        if request.method == 'OPTIONS' or request.path.startswith(self.RUTAS_EXENTAS):
            return None


        from seguridad_acceso.services import ip_esta_bloqueada

        ip = _obtener_ip(request)
        if ip and ip_esta_bloqueada(ip):
            return JsonResponse({'detail': 'Tu dirección IP está temporalmente bloqueada por seguridad.'}, status=423)
        return None
