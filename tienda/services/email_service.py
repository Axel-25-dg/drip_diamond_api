from django.template.loader import render_to_string

from tienda.services.resend_service import enviar_correo_resend


def _enviar(usuario, tipo, asunto, mensaje_corto, template, contexto):
    from tienda.models import Notificacion

    mensaje_html = render_to_string(template, contexto)
    notificacion = Notificacion.objects.create(
        usuario=usuario, tipo=tipo, asunto=asunto, mensaje_corto=mensaje_corto,
    )

    enviado = enviar_correo_resend(destinatario=usuario.email, asunto=asunto, html=mensaje_html)
    if enviado:
        notificacion.correo_enviado = True
        notificacion.save(update_fields=['correo_enviado'])

    return notificacion


def notificar_solicitud_compra(pedido):
    return _enviar(
        pedido.usuario, 'SOLICITUD_COMPRA', f'Recibimos tu solicitud — Pedido #{pedido.id}',
        'Te contactaremos para coordinar el pago.',
        'emails/solicitud_compra.html', {'pedido': pedido},
    )


def notificar_comprobante_recibido(pedido):
    return _enviar(
        pedido.usuario, 'COMPROBANTE_RECIBIDO', f'Recibimos tu comprobante — Pedido #{pedido.id}',
        'Estamos verificando tu pago.',
        'emails/comprobante_recibido.html', {'pedido': pedido},
    )


def notificar_pago_verificado(pedido):
    return _enviar(
        pedido.usuario, 'PAGO_VERIFICADO', f'Pago verificado — Pedido #{pedido.id}',
        'Ya estamos preparando tu pedido.',
        'emails/pago_verificado.html', {'pedido': pedido},
    )


def notificar_pago_rechazado(pedido):
    return _enviar(
        pedido.usuario, 'PAGO_RECHAZADO', f'Tu comprobante fue rechazado — Pedido #{pedido.id}',
        'Vuelve a subir un comprobante válido.',
        'emails/pago_rechazado.html', {'pedido': pedido},
    )


def notificar_pedido_enviado(pedido):
    return _enviar(
        pedido.usuario, 'PEDIDO_ENVIADO', f'Tu pedido va en camino — Pedido #{pedido.id}',
        f'Código de seguimiento: {pedido.numero_guia}',
        'emails/pedido_enviado.html', {'pedido': pedido},
    )


def notificar_pedido_entregado(pedido):
    return _enviar(
        pedido.usuario, 'PEDIDO_ENTREGADO', f'Pedido completado — #{pedido.id}',
        '¡Gracias por tu compra!',
        'emails/pedido_entregado.html', {'pedido': pedido},
    )


def enviar_ticket_compra(pedido):
    return _enviar(
        pedido.usuario, 'PAGO_VERIFICADO', f'Ticket de compra — Pedido #{pedido.id}',
        'Adjuntamos el detalle de tu compra.',
        'emails/ticket_compra.html', {'pedido': pedido},
    )


def notificar_comision_pagada(liquidacion):
    return _enviar(
        liquidacion.vendedor, 'COMISION_PAGADA',
        f'Tu comisión de {liquidacion.periodo_mes}/{liquidacion.periodo_anio} fue pagada',
        f'Total pagado: ${liquidacion.total_comisiones}',
        'emails/comision_pagada.html', {'liquidacion': liquidacion},
    )


def notificar_promocion(usuario, producto, promocion):
    return _enviar(
        usuario, 'PROMOCION', f'¡Promoción! {producto.nombre}',
        f'Ahora a ${promocion.precio_promocional}',
        'emails/promocion.html', {'producto': producto, 'promocion': promocion},
    )


def notificar_recuperar_password(usuario, enlace):
    return _enviar(
        usuario, 'RECUPERAR_PASSWORD', 'Recupera tu contraseña',
        'Sigue el enlace que te enviamos por correo.',
        'emails/recuperar_password.html', {'usuario': usuario, 'enlace': enlace},
    )


def notificar_alerta_seguridad(usuario, detalle):
    return _enviar(
        usuario, 'ALERTA_SEGURIDAD', 'Alerta de seguridad en tu cuenta',
        detalle,
        'emails/alerta_seguridad.html', {'usuario': usuario, 'detalle': detalle},
    )
