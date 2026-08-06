from django.db import models


class DireccionEnvioPedido(models.Model):
    """
    La dirección REFERENCIAL vive en Usuario.direccion_referencial (se pide
    en el registro). Esta es la dirección EXACTA que se captura en cada
    compra vía Google Maps (Geocoding/Places), ligada a ese pedido puntual.
    """
    pedido = models.OneToOneField('tienda.Pedido', on_delete=models.CASCADE, related_name='direccion_envio')
    direccion_formateada = models.CharField(max_length=255)
    referencia_adicional = models.CharField(max_length=255, blank=True, help_text='Ej: casa azul, junto a la tienda X')
    ciudad = models.CharField(max_length=100)
    latitud = models.DecimalField(max_digits=10, decimal_places=7)
    longitud = models.DecimalField(max_digits=10, decimal_places=7)
    place_id = models.CharField(max_length=150, blank=True)

    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dirección de Envío'
        verbose_name_plural = 'Direcciones de Envío'

    def __str__(self):
        return f'{self.direccion_formateada} (pedido #{self.pedido_id})'
