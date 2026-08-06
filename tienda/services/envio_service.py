"""
NO se integra ninguna API de paquetería (se descartó Servientrega
explícitamente). El costo lo define el administrador manualmente
(Pedido.costo_envio, sugerido desde CostoEnvioZona). Aquí solo se genera
un código interno de referencia que se le informa al cliente por correo.
"""
import random
import string


def _generar_numero_guia() -> str:
    return 'ZAP' + ''.join(random.choices(string.digits, k=10))


def marcar_pedido_enviado(pedido, usuario_responsable=None):
    """
    Se llama manualmente por el administrador cuando el paquete ya salió
    físicamente. Genera el código interno y dispara correo + notificación.
    """
    from tienda.models import EstadoPedido
    from tienda.services.email_service import notificar_pedido_enviado

    if not pedido.numero_guia:
        pedido.numero_guia = _generar_numero_guia()
        pedido.save(update_fields=['numero_guia'])

    pedido.cambiar_estado(EstadoPedido.ENVIADO, comentario='Pedido despachado', usuario_responsable=usuario_responsable)
    notificar_pedido_enviado(pedido)
    return pedido
