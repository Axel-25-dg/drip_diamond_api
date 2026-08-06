from django.urls import re_path

from tienda.consumers.chat_pedido_consumer import ChatPedidoConsumer

websocket_urlpatterns = [
    re_path(r'ws/pedidos/(?P<pedido_id>\d+)/chat/$', ChatPedidoConsumer.as_asgi()),
]
