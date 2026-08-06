from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class TipoEntrega(models.TextChoices):
    DOMICILIO = 'DOMICILIO', 'Entrega a domicilio'
    RETIRO_LOCAL = 'RETIRO_LOCAL', 'Retiro en local'


class EstadoPedido(models.TextChoices):
    CARRITO = 'CARRITO', 'Carrito'
    PENDIENTE_DE_PAGO = 'PENDIENTE_DE_PAGO', 'Pendiente de pago'
    COMPROBANTE_ENVIADO = 'COMPROBANTE_ENVIADO', 'Comprobante enviado'
    PAGO_EN_REVISION = 'PAGO_EN_REVISION', 'Pago en revisión'
    PAGO_APROBADO = 'PAGO_APROBADO', 'Pago aprobado'
    PAGO_RECHAZADO = 'PAGO_RECHAZADO', 'Pago rechazado'
    PREPARANDO_PEDIDO = 'PREPARANDO_PEDIDO', 'Preparando pedido'
    ENVIADO = 'ENVIADO', 'Enviado'
    ENTREGADO = 'ENTREGADO', 'Venta finalizada / Entregado'
    CANCELADO = 'CANCELADO', 'Cancelado'


TRANSICIONES_VALIDAS = {
    EstadoPedido.CARRITO: {EstadoPedido.PENDIENTE_DE_PAGO, EstadoPedido.CANCELADO},
    EstadoPedido.PENDIENTE_DE_PAGO: {EstadoPedido.COMPROBANTE_ENVIADO, EstadoPedido.CANCELADO},
    EstadoPedido.COMPROBANTE_ENVIADO: {EstadoPedido.PAGO_EN_REVISION, EstadoPedido.PAGO_APROBADO, EstadoPedido.PAGO_RECHAZADO, EstadoPedido.CANCELADO},
    EstadoPedido.PAGO_EN_REVISION: {EstadoPedido.PAGO_APROBADO, EstadoPedido.PAGO_RECHAZADO, EstadoPedido.CANCELADO},
    EstadoPedido.PAGO_RECHAZADO: {EstadoPedido.COMPROBANTE_ENVIADO, EstadoPedido.CANCELADO},
    EstadoPedido.PAGO_APROBADO: {EstadoPedido.PREPARANDO_PEDIDO, EstadoPedido.ENVIADO, EstadoPedido.CANCELADO},
    EstadoPedido.PREPARANDO_PEDIDO: {EstadoPedido.ENVIADO, EstadoPedido.CANCELADO},
    EstadoPedido.ENVIADO: {EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO},
    EstadoPedido.ENTREGADO: set(),
    EstadoPedido.CANCELADO: set(),
}


class Pedido(models.Model):
    """
    Eje central de la venta.
    Si el vendedor es null ("Ningún vendedor"), la venta NO genera comisión.
    Si hay un vendedor asignado, se genera la comisión fija de 4 USD únicamente al pasar a ENTREGADO.
    """
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='pedidos')
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ventas_como_vendedor',
        limit_choices_to={'rol': 'VENDEDOR'},
        help_text='Vendedor asignado. Si es nulo ("Ningún vendedor"), no genera comisión.',
    )

    tipo_entrega = models.CharField(max_length=20, choices=TipoEntrega.choices, default=TipoEntrega.DOMICILIO)

    costo_envio = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    costo_envio_definido = models.BooleanField(default=False)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    estado = models.CharField(max_length=25, choices=EstadoPedido.choices, default=EstadoPedido.PENDIENTE_DE_PAGO)

    numero_guia = models.CharField(max_length=30, blank=True, help_text='Código informativo enviado por correo')

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-creado_en']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['usuario']),
            models.Index(fields=['vendedor']),
        ]

    def __str__(self):
        return f'Pedido #{self.pk} — {self.usuario} — {self.get_estado_display()}'

    def cambiar_estado(self, nuevo_estado, comentario='', usuario_responsable=None):
        from tienda.models.historial import HistorialEstadoPedido

        if self.estado != nuevo_estado:
            permitidos = TRANSICIONES_VALIDAS.get(self.estado, set())
            if nuevo_estado not in permitidos:
                raise ValidationError(
                    f'Transición de estado inválida: de "{self.get_estado_display()}" a "{nuevo_estado}".'
                )

        self.estado = nuevo_estado
        self.save(update_fields=['estado', 'actualizado_en'])
        HistorialEstadoPedido.objects.create(
            pedido=self, estado=nuevo_estado, comentario=comentario, usuario_responsable=usuario_responsable
        )

    def recalcular_total(self):
        self.total = self.subtotal + self.costo_envio
        self.save(update_fields=['total'])


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    variante_producto = models.ForeignKey('tienda.VarianteProducto', on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Detalle de Pedido'
        verbose_name_plural = 'Detalles de Pedido'

    def __str__(self):
        return f'{self.cantidad} x {self.variante_producto} (pedido #{self.pedido_id})'
