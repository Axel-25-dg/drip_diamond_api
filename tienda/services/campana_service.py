from decimal import Decimal
from django.utils import timezone


def _obtener_destinatarios(segmento: str):
    """
    Retorna el queryset de usuarios según el segmento de la campaña.
    """
    from tienda.models import Rol, Usuario

    qs = Usuario.objects.filter(is_active=True)

    match segmento:
        case 'TODOS_LOS_CLIENTES':
            return qs.filter(rol=Rol.CLIENTE)
        case 'VENDEDORES':
            return qs.filter(rol=Rol.VENDEDOR)
        case 'CONTADORES':
            return qs.filter(rol=Rol.CONTADOR)
        case 'CLIENTES_CON_COMPRAS':
            from tienda.models import Pedido, EstadoPedido
            ids = Pedido.objects.filter(
                estado=EstadoPedido.ENTREGADO
            ).values_list('usuario_id', flat=True).distinct()
            return qs.filter(rol=Rol.CLIENTE, pk__in=ids)
        case 'CLIENTES_SIN_COMPRAS':
            from tienda.models import Pedido, EstadoPedido
            ids_con_compra = Pedido.objects.filter(
                estado=EstadoPedido.ENTREGADO
            ).values_list('usuario_id', flat=True).distinct()
            return qs.filter(rol=Rol.CLIENTE).exclude(pk__in=ids_con_compra)
        case _:
            return qs.none()


def enviar_campana(campana_id: int) -> dict:
    """
    Punto de entrada para enviar una campaña masiva.
    Itera por cada destinatario del segmento y envía el correo via Resend.
    Actualiza los contadores de enviados/fallidos en el modelo.

    Diseñado para ejecutarse en background (Celery task o llamada directa).
    Devuelve un resumen del resultado.
    """
    from tienda.models import CampanaEmail, EstadoCampana
    from tienda.services.resend_service import enviar_correo_resend

    campana = CampanaEmail.objects.get(pk=campana_id)

    if campana.estado in (EstadoCampana.ENVIANDO, EstadoCampana.ENVIADO):
        return {'error': 'La campaña ya está en proceso o fue enviada.'}

    destinatarios = list(_obtener_destinatarios(campana.segmento))
    campana.estado = EstadoCampana.ENVIANDO
    campana.total_destinatarios = len(destinatarios)
    campana.total_enviados = 0
    campana.total_fallidos = 0
    campana.save(update_fields=['estado', 'total_destinatarios', 'total_enviados', 'total_fallidos'])

    enviados = 0
    fallidos = 0

    for usuario in destinatarios:
        ok = enviar_correo_resend(
            destinatario=usuario.email,
            asunto=campana.asunto,
            html=campana.contenido_html,
        )
        if ok:
            enviados += 1
        else:
            fallidos += 1

    campana.estado = EstadoCampana.ENVIADO if fallidos == 0 else (
        EstadoCampana.FALLIDO if enviados == 0 else EstadoCampana.ENVIADO
    )
    campana.total_enviados = enviados
    campana.total_fallidos = fallidos
    campana.enviada_en = timezone.now()
    campana.save(update_fields=['estado', 'total_enviados', 'total_fallidos', 'enviada_en'])

    return {
        'campana_id': campana.id,
        'total_destinatarios': len(destinatarios),
        'enviados': enviados,
        'fallidos': fallidos,
        'estado': campana.estado,
    }
