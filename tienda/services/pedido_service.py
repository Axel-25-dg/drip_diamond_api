from decimal import Decimal

from django.db import transaction


class CarritoVacioError(Exception):
    pass


class StockInsuficienteError(Exception):
    pass


def _costo_envio_sugerido(ciudad: str, tipo_entrega: str) -> Decimal:
    """Busca el costo editado por el admin para esa ciudad; si no existe, 0 (el admin deberá definirlo antes de avanzar)."""
    from tienda.models import CostoEnvioZona, TipoEntrega

    zona = CostoEnvioZona.objects.filter(ciudad__iexact=ciudad, activo=True).first()
    if not zona:
        return Decimal('0')
    return zona.costo_domicilio if tipo_entrega == TipoEntrega.DOMICILIO else zona.costo_retiro_local


@transaction.atomic
def crear_pedido_desde_carrito(usuario, vendedor, tipo_entrega, direccion_data):
    """
    Convierte el carrito en un Pedido en estado PENDIENTE_DE_PAGO.
    """
    from tienda.models import Carrito, DetallePedido, DireccionEnvioPedido, EstadoPedido, Pedido

    carrito = Carrito.objects.prefetch_related('items__variante_producto__producto').get(usuario=usuario)
    items = list(carrito.items.select_related('variante_producto__producto'))
    if not items:
        raise CarritoVacioError('El carrito está vacío.')

    subtotal = Decimal('0')
    for item in items:
        variante = item.variante_producto
        if variante.stock < item.cantidad:
            raise StockInsuficienteError(f'Stock insuficiente para {variante}.')
        subtotal += variante.producto.precio_actual * item.cantidad

    costo_envio = _costo_envio_sugerido(direccion_data['ciudad'], tipo_entrega)

    pedido = Pedido.objects.create(
        usuario=usuario,
        vendedor=vendedor,
        tipo_entrega=tipo_entrega,
        subtotal=subtotal,
        costo_envio=costo_envio,
        costo_envio_definido=costo_envio > 0,
        total=subtotal + costo_envio,
        estado=EstadoPedido.PENDIENTE_DE_PAGO,
    )

    DireccionEnvioPedido.objects.create(pedido=pedido, **direccion_data)

    for item in items:
        variante = item.variante_producto
        DetallePedido.objects.create(
            pedido=pedido,
            variante_producto=variante,
            cantidad=item.cantidad,
            precio_unitario=variante.producto.precio_actual,
            subtotal=variante.producto.precio_actual * item.cantidad,
        )
        variante.stock -= item.cantidad
        variante.save(update_fields=['stock'])

    carrito.items.all().delete()
    pedido.cambiar_estado(EstadoPedido.PENDIENTE_DE_PAGO, comentario='Pedido registrado. Pendiente de pago por transferencia.', usuario_responsable=usuario)
    return pedido


def total_pares(pedido) -> int:
    return sum(d.cantidad for d in pedido.detalles.all())
