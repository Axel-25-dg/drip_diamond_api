import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='marcas/', null=True, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class CalidadProducto(models.TextChoices):
    ORIGINAL = 'ORIGINAL', 'Original'
    PRIMERA_CLASE = 'PRIMERA_CLASE', 'Full Quality'
    SEGUNDA_CLASE = 'SEGUNDA_CLASE', 'Calidad 1.1 Plus'


class Producto(models.Model):
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT, related_name='productos')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, related_name='productos')
    nombre = models.CharField(max_length=150)
    modelo = models.CharField(max_length=100, blank=True)
    codigo = models.CharField(max_length=60, unique=True, blank=True, null=True, help_text='Código único del producto; si no se envía, se genera automáticamente.')
    calidad = models.CharField(max_length=20, choices=CalidadProducto.choices, default=CalidadProducto.ORIGINAL)
    descripcion = models.TextField(blank=True)
    precio_base = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    imagen_principal = models.ImageField(upload_to='productos/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-creado_en']
        indexes = [models.Index(fields=['marca']), models.Index(fields=['activo'])]

    def save(self, *args, **kwargs):
        if not self.codigo:
            base = self.nombre or 'PRODUCTO'
            self.codigo = f'ZAP-{base[:4].upper().replace(" ", "")}-{uuid.uuid4().hex[:4].upper()}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.marca} {self.nombre} ({self.get_calidad_display()})'

    @property
    def stock_total(self):
        return sum(v.stock for v in self.variantes.all())

    @property
    def disponible(self):
        return self.activo and self.stock_total > 0

    @property
    def promocion_vigente(self):
        ahora = timezone.now()
        return self.promociones.filter(activo=True, fecha_inicio__lte=ahora, fecha_fin__gte=ahora).first()

    @property
    def precio_actual(self):
        promo = self.promocion_vigente
        return promo.precio_promocional if promo else self.precio_base


class Talla(models.Model):
    valor = models.CharField(max_length=10, unique=True, help_text='Ej: 38, 39, 40...')

    class Meta:
        verbose_name = 'Talla'
        verbose_name_plural = 'Tallas'
        ordering = ['valor']

    def __str__(self):
        return self.valor


class VarianteProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='variantes')
    talla = models.ForeignKey(Talla, on_delete=models.PROTECT, related_name='variantes')
    stock = models.PositiveIntegerField(default=9999)
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)])
    sku = models.CharField(max_length=40, unique=True)

    class Meta:
        verbose_name = 'Variante de Producto'
        verbose_name_plural = 'Variantes de Producto'
        unique_together = ('producto', 'talla')

    def __str__(self):
        return f'{self.producto} — talla {self.talla} ({self.stock} unid.)'

    @property
    def disponible(self):
        return self.stock > 0


class Promocion(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='promociones')
    precio_promocional = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Promoción'
        verbose_name_plural = 'Promociones'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f'Promo {self.producto} → ${self.precio_promocional}'
