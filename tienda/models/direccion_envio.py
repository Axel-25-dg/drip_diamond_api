from django.db import models


class DireccionEnvioPedido(models.Model):
    pedido = models.OneToOneField('tienda.Pedido', on_delete=models.CASCADE, related_name='direccion_envio')
    direccion_formateada = models.CharField(max_length=255)
    referencia_adicional = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100, blank=True, default='')
    telefono_contacto = models.CharField(max_length=50, blank=True, default='')

    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Direccion de Envio'
        verbose_name_plural = 'Direcciones de Envio'

    def __str__(self):
        return f'{self.direccion_formateada} (pedido #{self.pedido_id})'
