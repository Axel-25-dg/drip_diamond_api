from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class TipoEntrega(models.TextChoices):
    DOMICILIO = 'DOMICILIO', 'Entrega a domicilio'
    RETIRO_LOCAL = 'RETIRO_LOCAL', 'Retiro en local'


class EstadoPedido(models.TextChoices):
    SOLICITADO = 'SOLICITADO', 'Compra solicitada'
    CONTACTADO = 'CONTACTADO', 'Cliente contactado'
    PAGO_SUBIDO = 'PAGO_SUBIDO', 'Comprobante subido'
    PAGO_VERIFICADO = 'PAGO_VERIFICADO', 'Pago verificado'
    PAGO_RECHAZADO = 'PAGO_RECHAZADO', 'Pago rechazado'
    EN_PREPARACION = 'EN_PREPARACION', 'En preparación'
    ENVIADO = 'ENVIADO', 'Enviado'
    ENTREGADO = 'ENTREGADO', 'Entregado y confirmado'
    CANCELADO = 'CANCELADO', 'Cancelado'


class Pedido(models.Model):
    """
    Eje central. IMPORTANTE: la comisión del vendedor NO se genera aquí ni
    al verificar el pago — solo se genera cuando el estado pasa a ENTREGADO
    a través de la confirmación manual del contador (ver services/comision_service.py).
    """
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='pedidos')
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='ventas_como_vendedor',
        limit_choices_to={'rol': 'VENDEDOR'},
        help_text='Obligatorio: requisito para que se le pueda pagar la comisión',
    )

    tipo_entrega = models.CharField(max_length=20, choices=TipoEntrega.choices, default=TipoEntrega.DOMICILIO)

    # Costo de envío: SIEMPRE manual (sin API de paquetería). Lo define el
    # administrador según distancia/ciudad antes de que el pedido avance.
    costo_envio = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    costo_envio_definido = models.BooleanField(default=False)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    estado = models.CharField(max_length=20, choices=EstadoPedido.choices, default=EstadoPedido.SOLICITADO)

    numero_guia = models.CharField(max_length=30, blank=True, help_text='Código informativo enviado por correo, sin integración de paquetería')

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
