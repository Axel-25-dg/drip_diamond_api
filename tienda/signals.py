from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone


# ------------------------------------------------------------------
# Usuario: username automático + forzar 2FA en roles críticos
# ------------------------------------------------------------------
@receiver(pre_save, sender='tienda.Usuario')
def autogenerar_username_y_2fa(sender, instance, **kwargs):
    from tienda.models import Rol
    from tienda.services.username_service import generar_username

    if not instance.username:
        instance.username = generar_username(instance.primer_nombre, instance.primer_apellido)

    if instance.rol in (Rol.ADMINISTRADOR, Rol.CONTADOR):
        instance.doble_factor_activo = True


# ------------------------------------------------------------------
# Pedido: al crearse, notificar la solicitud de compra
# ------------------------------------------------------------------
@receiver(post_save, sender='tienda.Pedido')
def notificar_pedido_creado(sender, instance, created, **kwargs):
    if created:
        from tienda.services.email_service import notificar_solicitud_compra
        notificar_solicitud_compra(instance)


# ------------------------------------------------------------------
# Comprobante de pago: al verificar, factura automática + correo.
# La comisión del vendedor NO se toca aquí (ver services/comision_service.py,
# solo se dispara cuando se pasa a ENTREGADO).
# ------------------------------------------------------------------
@receiver(pre_save, sender='tienda.ComprobantePago')
def procesar_cambio_estado_comprobante(sender, instance, **kwargs):
    from tienda.models import ComprobantePago, EstadoComprobante, EstadoPedido

    if not instance.pk:
        return

    anterior = ComprobantePago.objects.get(pk=instance.pk)
    if anterior.estado == instance.estado:
        return

    pedido = instance.pedido

    if instance.estado == EstadoComprobante.VERIFICADO:
        instance.fecha_verificacion = timezone.now()
        pedido.cambiar_estado(
            EstadoPedido.PAGO_APROBADO, comentario='Comprobante de pago verificado y aprobado por contabilidad',
            usuario_responsable=instance.verificado_por,
        )

        from tienda.services.contabilidad_service import generar_factura_por_pedido
        from tienda.services.email_service import enviar_ticket_compra, notificar_pago_verificado

        generar_factura_por_pedido(pedido)
        notificar_pago_verificado(pedido)
        enviar_ticket_compra(pedido)

    elif instance.estado == EstadoComprobante.RECHAZADO:
        pedido.cambiar_estado(
            EstadoPedido.PAGO_RECHAZADO, comentario=instance.observacion,
            usuario_responsable=instance.verificado_por,
        )
        from tienda.services.email_service import notificar_pago_rechazado
        notificar_pago_rechazado(pedido)
