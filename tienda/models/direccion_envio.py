from django.db import models


class DireccionEnvioPedido(models.Model):
    """
    La dirección REFERENCIAL vive en Usuario.direccion_referencial (se pide
    en el registro). Esta es la dirección EXACTA del pedido, con detalles de
    vivienda y referencias específicas para la entrega.
    """
    pedido = models.OneToOneField('tienda.Pedido', on_delete=models.CASCADE, related_name='direccion_envio')
    direccion_formateada = models.CharField(max_length=255)
    referencia_adicional = models.CharField(max_length=255, blank=True, help_text='Ej: casa azul, junto a la tienda X')
    ciudad = models.CharField(max_length=100)

    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dirección de Envío'
        verbose_name_plural = 'Direcciones de Envío'

    def __str__(self):
        return f'{self.direccion_formateada} (pedido #{self.pedido_id})'
