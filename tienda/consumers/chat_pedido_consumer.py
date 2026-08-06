import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatPedidoConsumer(AsyncWebsocketConsumer):
    """
    Un canal por pedido: ws/pedidos/<pedido_id>/chat/?token=<jwt>

    Mensajes que acepta (JSON):
      {"tipo": "mensaje", "texto": "..."}
      {"tipo": "confirmar_entrega"}   -> SOLO el contador puede enviarlo;
                                          dispara comision_service.confirmar_entrega_y_generar_comision
    """

    async def connect(self):
        self.pedido_id = self.scope['url_route']['kwargs']['pedido_id']
        self.grupo = f'chat_pedido_{self.pedido_id}'
        usuario = self.scope['user']

        if not usuario or not usuario.is_authenticated:
            await self.close()
            return

        permitido = await self._usuario_autorizado(usuario, self.pedido_id)
        if not permitido:
            await self.close()
            return

        await self.channel_layer.group_add(self.grupo, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.grupo, self.channel_name)

    async def receive(self, text_data):
        datos = json.loads(text_data)
        usuario = self.scope['user']

        if datos.get('tipo') == 'confirmar_entrega':
            await self._procesar_confirmacion(usuario)
            return

        texto = datos.get('texto', '').strip()
        if not texto:
            return

        mensaje = await self._guardar_mensaje(usuario, texto)
        await self.channel_layer.group_send(self.grupo, {
            'type': 'chat_mensaje',
            'data': {
                'tipo': 'mensaje', 'remitente': usuario.nombre_completo,
                'remitente_id': usuario.id, 'texto': texto, 'fecha': mensaje.enviado_en.isoformat(),
            },
        })

    async def _procesar_confirmacion(self, usuario):
        if not getattr(usuario, 'es_contador', False):
            await self.send(text_data=json.dumps({'tipo': 'error', 'detalle': 'Solo el contador puede confirmar la entrega.'}))
            return

        resultado = await self._confirmar_entrega(usuario)
        await self.channel_layer.group_send(self.grupo, {
            'type': 'chat_mensaje',
            'data': {'tipo': 'entrega_confirmada', 'detalle': resultado},
        })

    # -- helpers de base de datos --

    @database_sync_to_async
    def _usuario_autorizado(self, usuario, pedido_id):
        from tienda.models import Pedido

        pedido = Pedido.objects.filter(pk=pedido_id).first()
        if not pedido:
            return False
        return usuario.es_administrador or usuario.es_contador or pedido.vendedor_id == usuario.id or pedido.usuario_id == usuario.id

    @database_sync_to_async
    def _guardar_mensaje(self, usuario, texto):
        from tienda.models import MensajeChatPedido

        return MensajeChatPedido.objects.create(pedido_id=self.pedido_id, remitente=usuario, mensaje=texto)

    @database_sync_to_async
    def _confirmar_entrega(self, contador):
        from tienda.models import MensajeChatPedido, Pedido
        from tienda.services.comision_service import (
            EntregaYaConfirmadaError,
            PedidoNoEnviadoError,
            confirmar_entrega_y_generar_comision,
        )

        pedido = Pedido.objects.get(pk=self.pedido_id)
        try:
            comision = confirmar_entrega_y_generar_comision(pedido, contador)
        except (EntregaYaConfirmadaError, PedidoNoEnviadoError) as exc:
            return {'exito': False, 'mensaje': str(exc)}

        MensajeChatPedido.objects.create(
            pedido=pedido, remitente=contador,
            mensaje=f'Entrega confirmada. Comisión generada: ${comision.monto}',
            es_confirmacion_entrega=True,
        )
        return {'exito': True, 'mensaje': f'Entrega confirmada — comisión de ${comision.monto} generada para el vendedor.'}

    async def chat_mensaje(self, event):
        await self.send(text_data=json.dumps(event['data']))
