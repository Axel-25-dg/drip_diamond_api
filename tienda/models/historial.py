from django.conf import settings
from django.db import models


class HistorialEstadoPedido(models.Model):
    pedido = models.ForeignKey('tienda.Pedido', on_delete=models.CASCADE, related_name='historial')
    estado = models.CharField(max_length=20)
    comentario = models.CharField(max_length=255, blank=True)
    usuario_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cambios_estado_realizados',
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historial de Estado de Pedido'
        verbose_name_plural = 'Historial de Estados de Pedido'
        ordering = ['fecha']

    def __str__(self):
        return f'Pedido #{self.pedido_id} → {self.estado} ({self.fecha:%Y-%m-%d %H:%M})'
