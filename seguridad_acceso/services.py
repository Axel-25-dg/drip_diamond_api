from datetime import timedelta

from django.conf import settings
from django.utils import timezone


def ip_esta_bloqueada(ip) -> bool:
    from seguridad_acceso.models import IPBloqueada

    bloqueo = IPBloqueada.objects.filter(ip=ip).first()
    if not bloqueo:
        return False
    if bloqueo.desbloquear_en <= timezone.now():
        bloqueo.delete()
        return False
    return True


def registrar_intento_login(username: str, ip: str, exitoso: bool):
    from seguridad_acceso.models import IntentoLogin, IPBloqueada

    IntentoLogin.objects.create(username_intentado=username, ip=ip, exitoso=exitoso)

    if exitoso:
        return

    limite = timezone.now() - timedelta(minutes=settings.LOGIN_BLOQUEO_MINUTOS)
    fallidos_recientes = IntentoLogin.objects.filter(ip=ip, exitoso=False, fecha__gte=limite).count()

    if fallidos_recientes >= settings.LOGIN_MAX_INTENTOS:
        IPBloqueada.objects.get_or_create(
            ip=ip,
            defaults={
                'motivo': f'{fallidos_recientes} intentos fallidos en los últimos {settings.LOGIN_BLOQUEO_MINUTOS} minutos',
                'desbloquear_en': timezone.now() + timedelta(minutes=settings.LOGIN_BLOQUEO_MINUTOS),
            },
        )


def registrar_auditoria(usuario, accion: str, modelo_afectado='', objeto_id='', detalle='', ip=None):
    from seguridad_acceso.models import LogAuditoria

    LogAuditoria.objects.create(
        usuario=usuario, accion=accion, modelo_afectado=modelo_afectado,
        objeto_id=str(objeto_id), detalle=detalle, ip=ip,
    )
