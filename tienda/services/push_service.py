import json
import logging
from pywebpush import webpush, WebPushException
from tienda.models import SuscripcionPush, CampanaNotificacionPush, Rol
from tienda.utils.vapid_utils import obtener_o_generar_llaves_vapid

logger = logging.getLogger(__name__)


def enviar_notificacion_push_suscripcion(suscripcion, titulo, cuerpo, url_destino='/', imagen_url='', icono_url='', badge_url='', data=None):
    """
    Envía una notificación nativa del sistema a una suscripción Web Push individual.
    Maneja la desactiva automática de suscripciones caducadas (404/410).
    """
    if not suscripcion.activa:
        return False

    public_key, private_key, claim_email = obtener_o_generar_llaves_vapid()

    # Construir payload enriquecido estilo Google App
    payload = {
        'title': titulo,
        'body': cuerpo,
        'icon': icono_url or '/static/img/icon-192.png',
        'image': imagen_url or None,
        'badge': badge_url or '/static/img/badge-72.png',
        'data': {
            'url': url_destino,
            'timestamp': suscripcion.creada_en.isoformat() if suscripcion.creada_en else None,
            **(data or {})
        },
        'vibrate': [200, 100, 200, 100, 200],
        'renotify': True,
        'tag': f'zapatillas-push-{suscripcion.id}',
        'actions': [
            {'action': 'open_url', 'title': 'Ver detalles'},
            {'action': 'dismiss', 'title': 'Cerrar'}
        ]
    }

    sub_info = {
        'endpoint': suscripcion.endpoint,
        'keys': {
            'p256dh': suscripcion.p256dh,
            'auth': suscripcion.auth
        }
    }

    try:
        webpush(
            subscription_info=sub_info,
            data=json.dumps(payload),
            vapid_private_key=private_key,
            vapid_claims={'sub': claim_email},
            ttl=86400  # 24 horas de vigencia en servidor push
        )
        logger.info(f"Notificación Push entregada a {suscripcion}")
        return True

    except WebPushException as ex:
        logger.warning(f"Error enviando Web Push a {suscripcion}: {ex}")
        response = getattr(ex, 'response', None)
        status_code = response.status_code if response else None

        # Si la suscripción venció o el usuario revocó permisos (404 Not Found / 410 Gone)
        if status_code in (404, 410):
            suscripcion.activa = False
            suscripcion.save(update_fields=['activa'])
            logger.info(f"Suscripción Push desactivada automáticamente por caducidad ({status_code}): {suscripcion.id}")

        return False
    except Exception as e:
        logger.error(f"Excepción inesperada en Push Service: {e}")
        return False


def enviar_push_a_usuario(usuario, titulo, cuerpo, url_destino='/', imagen_url='', icono_url='', data=None):
    """
    Envía una notificación Push del sistema a TODOS los dispositivos activos de un usuario específico.
    """
    if not usuario:
        return 0

    suscripciones = SuscripcionPush.objects.filter(usuario=usuario, activa=True)
    if not suscripciones.exists():
        return 0

    exitosos = 0
    for sub in suscripciones:
        if enviar_notificacion_push_suscripcion(
            suscripcion=sub,
            titulo=titulo,
            cuerpo=cuerpo,
            url_destino=url_destino,
            imagen_url=imagen_url,
            icono_url=icono_url,
            data=data
        ):
            exitosos += 1

    return exitosos


def broadcast_push_campana(campana: CampanaNotificacionPush):
    """
    Despacha una campaña masiva o personalizada creada por un Administrador
    hacia los dispositivos objetivo.
    """
    queryset = SuscripcionPush.objects.filter(activa=True)

    if campana.segmento == 'CLIENTES':
        queryset = queryset.filter(usuario__rol=Rol.CLIENTE)
    elif campana.segmento == 'VENDEDORES':
        queryset = queryset.filter(usuario__rol=Rol.VENDEDOR)
    elif campana.segmento == 'ESPECIFICOS':
        usuarios_ids = campana.usuarios_especificos.values_list('id', flat=True)
        queryset = queryset.filter(usuario_id__in=usuarios_ids)

    suscripciones = list(queryset)
    total = len(suscripciones)
    exitosos = 0
    fallidos = 0

    for sub in suscripciones:
        ok = enviar_notificacion_push_suscripcion(
            suscripcion=sub,
            titulo=campana.titulo,
            cuerpo=campana.cuerpo,
            url_destino=campana.url_destino,
            imagen_url=campana.imagen_url,
            icono_url=campana.icono_url,
            badge_url=campana.badge_url,
            data={'campana_id': campana.id}
        )
        if ok:
            exitosos += 1
        else:
            fallidos += 1

    campana.total_enviados = total
    campana.total_exitosos = exitosos
    campana.total_fallidos = fallidos
    campana.save(update_fields=['total_enviados', 'total_exitosos', 'total_fallidos'])

    return {
        'total': total,
        'exitosos': exitosos,
        'fallidos': fallidos
    }
