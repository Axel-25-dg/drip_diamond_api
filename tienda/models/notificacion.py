from django.conf import settings
from django.db import models


class TipoNotificacion(models.TextChoices):
    SOLICITUD_COMPRA = 'SOLICITUD_COMPRA', 'Compra solicitada'
    COMPROBANTE_RECIBIDO = 'COMPROBANTE_RECIBIDO', 'Comprobante recibido'
    PAGO_VERIFICADO = 'PAGO_VERIFICADO', 'Pago verificado'
    PAGO_RECHAZADO = 'PAGO_RECHAZADO', 'Pago rechazado'
    PEDIDO_ENVIADO = 'PEDIDO_ENVIADO', 'Pedido enviado'
    PEDIDO_ENTREGADO = 'PEDIDO_ENTREGADO', 'Pedido entregado'
    COMISION_PAGADA = 'COMISION_PAGADA', 'Comisión pagada'
    PROMOCION = 'PROMOCION', 'Promoción'
    RECUPERAR_PASSWORD = 'RECUPERAR_PASSWORD', 'Recuperación de contraseña'
    ALERTA_SEGURIDAD = 'ALERTA_SEGURIDAD', 'Alerta de seguridad'


class Notificacion(models.Model):
    """
    Se crea siempre junto a cada correo enviado (ver services/email_service.py),
    con el mismo motivo, para que el usuario la vea también dentro de la app.
    """
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=25, choices=TipoNotificacion.choices)
    asunto = models.CharField(max_length=150)
    mensaje_corto = models.CharField(max_length=255)
    correo_enviado = models.BooleanField(default=False)
    leida = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-creada_en']

    def __str__(self):
        return f'{self.get_tipo_display()} → {self.usuario}'
