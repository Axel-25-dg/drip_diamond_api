from decimal import Decimal

from django.conf import settings
from django.db import transaction


def _siguiente_numero_secuencial():
    from tienda.models import Factura

    ultima = Factura.objects.order_by('-id').first()
    siguiente = (ultima.id + 1) if ultima else 1
    return f'001-001-{siguiente:09d}'


def generar_factura_por_pedido(pedido):
    """Automático al verificarse el pago (ver signals.py). El contador no interviene."""
    from tienda.models import Factura

    if hasattr(pedido, 'factura'):
        return pedido.factura

    iva_porcentaje = Decimal(str(settings.IVA_PORCENTAJE))
    iva_valor = (pedido.subtotal * iva_porcentaje / 100).quantize(Decimal('0.01'))
    total = pedido.subtotal + iva_valor + pedido.costo_envio

    return Factura.objects.create(
        pedido=pedido,
        numero_secuencial=_siguiente_numero_secuencial(),
        subtotal=pedido.subtotal,
        iva_porcentaje=iva_porcentaje,
        iva_valor=iva_valor,
        total=total,
    )


@transaction.atomic
def cerrar_libro_ventas_mensual(anio, mes):
    """Puede ejecutarse por tarea programada (cron/Celery) — no requiere acción manual del contador."""
    from tienda.models import Factura, LibroVentas, ReporteSRI

    facturas_mes = Factura.objects.filter(generada_en__year=anio, generada_en__month=mes)
    total_ventas = sum((f.subtotal for f in facturas_mes), Decimal('0'))
    total_iva = sum((f.iva_valor for f in facturas_mes), Decimal('0'))

    libro, _ = LibroVentas.objects.get_or_create(anio=anio, mes=mes)
    libro.total_ventas = total_ventas
    libro.total_iva = total_iva
    libro.cerrado = True
    libro.save()

    reporte, _ = ReporteSRI.objects.get_or_create(libro_ventas=libro)
    return reporte
