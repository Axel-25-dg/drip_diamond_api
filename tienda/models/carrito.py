from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Carrito(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carrito')
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Carrito'
        verbose_name_plural = 'Carritos'

    def __str__(self):
        return f'Carrito de {self.usuario}'

    @property
    def subtotal(self):
        return sum((item.subtotal for item in self.items.all()), 0)


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name='items')
    variante_producto = models.ForeignKey('tienda.VarianteProducto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    agregado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ítem de Carrito'
        verbose_name_plural = 'Ítems de Carrito'
        unique_together = ('carrito', 'variante_producto')

    def __str__(self):
        return f'{self.cantidad} x {self.variante_producto}'

    @property
    def subtotal(self):
        return self.cantidad * self.variante_producto.producto.precio_actual
