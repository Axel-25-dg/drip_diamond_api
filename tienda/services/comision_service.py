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
    from tienda.models import ComisionVenta, EstadoPedido, LiquidacionMensual
    from tienda.models.comision import EstadoComision
    from tienda.services.email_service import notificar_pedido_entregado
    from tienda.services.pedido_service import total_pares

    if hasattr(pedido, 'comision'):
        raise EntregaYaConfirmadaError('Este pedido ya tiene la entrega confirmada.')

    if pedido.estado != EstadoPedido.ENVIADO:
        raise PedidoNoEnviadoError('El pedido debe estar en estado ENVIADO antes de confirmar la entrega.')

    comision = None

    if pedido.vendedor:
        pares = total_pares(pedido)
        monto_por_par = Decimal(str(settings.COMISION_FIJA_POR_PAR))
        monto_total = monto_por_par * pares
        ahora = timezone.localtime()

        # Si ya existe una liquidacion NO pagada para este mes, asignar directamente
        liq_existente = LiquidacionMensual.objects.filter(
            vendedor=pedido.vendedor,
            periodo_anio=ahora.year,
            periodo_mes=ahora.month,
            pagada=False,
        ).first()

        estado_comision = EstadoComision.LIQUIDADA if liq_existente else EstadoComision.PENDIENTE

        comision = ComisionVenta.objects.create(
            pedido=pedido,
            vendedor=pedido.vendedor,
            cantidad_pares=pares,
            monto_por_par=monto_por_par,
            monto=monto_total,
            confirmada_por=contador,
            estado=estado_comision,
            liquidacion=liq_existente,
        )

        if liq_existente:
            _recalcular_liquidacion(liq_existente)

    pedido.cambiar_estado(
        EstadoPedido.ENTREGADO,
        comentario='Entrega confirmada por el contador / Venta finalizada',
        usuario_responsable=contador,
    )
    notificar_pedido_entregado(pedido)
    return comision


def _recalcular_liquidacion(liquidacion):
    from django.db.models import Sum
    agg = liquidacion.comisiones.aggregate(tp=Sum('cantidad_pares'), tm=Sum('monto'))
    liquidacion.total_pares = agg['tp'] or 0
    liquidacion.total_comisiones = agg['tm'] or Decimal('0')
    liquidacion.save(update_fields=['total_pares', 'total_comisiones'])


@transaction.atomic
def generar_liquidacion_mensual(vendedor, anio, mes):
    from tienda.models import ComisionVenta, EstadoComision, LiquidacionMensual

    liquidacion, created = LiquidacionMensual.objects.get_or_create(
        vendedor=vendedor,
        periodo_anio=anio,
        periodo_mes=mes,
    )

    # Comisiones pendientes sin liquidacion del mes
    pendientes = ComisionVenta.objects.filter(
        vendedor=vendedor,
        generada_en__year=anio,
        generada_en__month=mes,
        liquidacion__isnull=True,
        estado=EstadoComision.PENDIENTE,
    )
    # Comisiones ya asignadas a esta liquidacion
    ya_asignadas = ComisionVenta.objects.filter(
        vendedor=vendedor,
        generada_en__year=anio,
        generada_en__month=mes,
        liquidacion=liquidacion,
    )

    # Asignar pendientes a la liquidacion
    pendientes.update(estado=EstadoComision.LIQUIDADA, liquidacion=liquidacion)

    # Recalcular totales con TODAS las comisiones del mes (ya asignadas + recien asignadas)
    _recalcular_liquidacion(liquidacion)

    return liquidacion


def marcar_liquidacion_pagada(liquidacion, contador, comprobante_pago):
    from tienda.services.email_service import notificar_comision_pagada

    liquidacion.comprobante_pago = comprobante_pago
    liquidacion.pagada = True
    liquidacion.marcada_pagada_por = contador
    liquidacion.fecha_pago = timezone.now()
    liquidacion.save(update_fields=['comprobante_pago', 'pagada', 'marcada_pagada_por', 'fecha_pago'])

    notificar_comision_pagada(liquidacion)
    return liquidacion
