from rest_framework import permissions
from rest_framework.generics import ListAPIView

from tienda.models import MensajeChatPedido
from tienda.serializers.venta_serializers import MensajeChatPedidoSerializer


class MensajesChatPedidoView(ListAPIView):
    """
    Historial de mensajes de un pedido (para cargar el chat al abrirlo;
    los mensajes nuevos llegan por WebSocket, ver tienda/consumers/).
    """
    serializer_class = MensajeChatPedidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MensajeChatPedido.objects.filter(pedido_id=self.kwargs['pedido_id']).select_related('remitente')
