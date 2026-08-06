from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone


class EntregaYaConfirmadaError(Exception):
    pass


class PedidoNoEnviadoError(Exception):
    pass


@transaction.atomic
def confirmar_entrega_y_generar_comision(pedido, contador):
    """
    ÚNICO punto del sistema donde se genera la comisión del vendedor.
    Se llama cuando el contador confirma, desde el chat en tiempo real del
    pedido, que el cliente ya recibió su paquete. Antes de esto no existe
    ningún registro de comisión para ese pedido.
    """
    from tienda.models import ComisionVenta, EstadoPedido
    from tienda.services.email_service import notificar_pedido_entregado
    from tienda.services.pedido_service import total_pares

    if hasattr(pedido, 'comision'):
        raise EntregaYaConfirmadaError('Este pedido ya tiene la entrega confirmada y su comisión generada.')

    if pedido.estado != EstadoPedido.ENVIADO:
        raise PedidoNoEnviadoError('El pedido debe estar en estado ENVIADO antes de confirmar la entrega.')

    pares = total_pares(pedido)
    monto_por_par = Decimal(str(settings.COMISION_FIJA_POR_PAR))
    monto_total = monto_por_par * pares

    comision = ComisionVenta.objects.create(
        pedido=pedido,
        vendedor=pedido.vendedor,
        cantidad_pares=pares,
        monto_por_par=monto_por_par,
        monto=monto_total,
        confirmada_por=contador,
    )

    pedido.cambiar_estado(EstadoPedido.ENTREGADO, comentario='Entrega confirmada por el contador', usuario_responsable=contador)
    notificar_pedido_entregado(pedido)
    return comision


@transaction.atomic
def generar_liquidacion_mensual(vendedor, anio, mes):
    from tienda.models import ComisionVenta, EstadoComision, LiquidacionMensual

    comisiones = ComisionVenta.objects.filter(
        vendedor=vendedor, estado=EstadoComision.PENDIENTE,
        generada_en__year=anio, generada_en__month=mes,
    )

    liquidacion, _ = LiquidacionMensual.objects.get_or_create(vendedor=vendedor, periodo_anio=anio, periodo_mes=mes)
    liquidacion.total_pares = sum((c.cantidad_pares for c in comisiones), 0)
    liquidacion.total_comisiones = sum((c.monto for c in comisiones), Decimal('0'))
    liquidacion.save(update_fields=['total_pares', 'total_comisiones'])

    comisiones.update(estado=EstadoComision.LIQUIDADA, liquidacion=liquidacion)
    return liquidacion


def marcar_liquidacion_pagada(liquidacion, contador, comprobante_pago):
    """
    Segunda y última acción manual del contador: marcar la liquidación
    como pagada una vez que el administrador ya hizo la transferencia.
    """
    from tienda.services.email_service import notificar_comision_pagada

    liquidacion.comprobante_pago = comprobante_pago
    liquidacion.pagada = True
    liquidacion.marcada_pagada_por = contador
    liquidacion.fecha_pago = timezone.now()
    liquidacion.save(update_fields=['comprobante_pago', 'pagada', 'marcada_pagada_por', 'fecha_pago'])

    notificar_comision_pagada(liquidacion)
    return liquidacion
