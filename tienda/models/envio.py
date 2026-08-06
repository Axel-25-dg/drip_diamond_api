from django.core.validators import MinValueValidator
from django.db import models


class CostoEnvioZona(models.Model):
    """
    Referencia editable por el administrador para sugerir el costo de envío
    según ciudad/zona y tipo de entrega. NO se consulta ninguna API externa
    de paquetería — el admin puede además sobreescribir el costo puntual de
    un pedido en Pedido.costo_envio.
    """
    ciudad = models.CharField(max_length=100, unique=True)
    costo_domicilio = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    costo_retiro_local = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Costo de Envío por Zona'
        verbose_name_plural = 'Costos de Envío por Zona'
        ordering = ['ciudad']

    def __str__(self):
        return f'{self.ciudad}: domicilio ${self.costo_domicilio} / retiro ${self.costo_retiro_local}'
