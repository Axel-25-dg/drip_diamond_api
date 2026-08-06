from django.conf import settings
from django.db import models


class MensajeChatPedido(models.Model):
    """
    Canal de chat (WebSocket, ver consumers/chat_pedido_consumer.py) sobre
    un pedido puntual. Sirve para coordinar la entrega; cuando el contador
    envía la acción de confirmación, se marca es_confirmacion_entrega=True
    y ESO dispara el cálculo de la comisión del vendedor.
    """
    pedido = models.ForeignKey('tienda.Pedido', on_delete=models.CASCADE, related_name='mensajes_chat')
    remitente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='mensajes_enviados')
    mensaje = models.TextField()
    es_confirmacion_entrega = models.BooleanField(default=False)
    enviado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mensaje de Chat de Pedido'
        verbose_name_plural = 'Mensajes de Chat de Pedido'
        ordering = ['enviado_en']

    def __str__(self):
        return f'Pedido #{self.pedido_id} — {self.remitente}: {self.mensaje[:40]}'
