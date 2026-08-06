from django.conf import settings
from django.db import models


class EstadoComprobante(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente de verificación'
    VERIFICADO = 'VERIFICADO', 'Verificado'
    RECHAZADO = 'RECHAZADO', 'Rechazado'


class ComprobantePago(models.Model):
    """
    El cliente lo sube desde la aplicación. Solo Administrador o Contador
    pueden verificarlo. Verificar dispara: factura automática + correo +
    notificación (ver tienda/signals.py). NO dispara la comisión todavía.
    """
    pedido = models.OneToOneField('tienda.Pedido', on_delete=models.CASCADE, related_name='comprobante_pago')
    archivo = models.FileField(upload_to='comprobantes_pago/%Y/%m/')
    banco_origen = models.CharField(max_length=100, blank=True)
    numero_referencia = models.CharField(max_length=50, blank=True)
    monto_declarado = models.DecimalField(max_digits=10, decimal_places=2)

    estado = models.CharField(max_length=15, choices=EstadoComprobante.choices, default=EstadoComprobante.PENDIENTE)
    verificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='comprobantes_verificados',
    )
    fecha_verificacion = models.DateTimeField(null=True, blank=True)
    observacion = models.TextField(blank=True)

    subido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comprobante de Pago'
        verbose_name_plural = 'Comprobantes de Pago'

    def __str__(self):
        return f'Comprobante pedido #{self.pedido_id} — {self.get_estado_display()}'
