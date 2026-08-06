from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class EstadoFacturaSRI(models.TextChoices):
    GENERADA = 'GENERADA', 'Generada'
    AUTORIZADA = 'AUTORIZADA', 'Autorizada SRI'
    ANULADA = 'ANULADA', 'Anulada'


class Factura(models.Model):
    """100% automática: se genera al verificarse el pago (ver signals.py). El contador no interviene aquí."""
    pedido = models.OneToOneField('tienda.Pedido', on_delete=models.PROTECT, related_name='factura')
    numero_secuencial = models.CharField(max_length=20, unique=True, editable=False)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    iva_porcentaje = models.DecimalField(max_digits=4, decimal_places=2, default=15)
    iva_valor = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    estado = models.CharField(max_length=15, choices=EstadoFacturaSRI.choices, default=EstadoFacturaSRI.GENERADA)
    clave_acceso_sri = models.CharField(max_length=49, blank=True)

    generada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-generada_en']

    def __str__(self):
        return f'Factura {self.numero_secuencial} — ${self.total}'


class NotaCredito(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.PROTECT, related_name='notas_credito')
    motivo = models.CharField(max_length=255)
    valor = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    generada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Nota de Crédito'
        verbose_name_plural = 'Notas de Crédito'

    def __str__(self):
        return f'Nota de crédito de {self.factura.numero_secuencial}'


class RetencionImpuesto(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.PROTECT, related_name='retenciones')
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    valor_retenido = models.DecimalField(max_digits=10, decimal_places=2)
    codigo_sri = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Retención de Impuesto'
        verbose_name_plural = 'Retenciones de Impuesto'

    def __str__(self):
        return f'Retención {self.porcentaje}% sobre {self.factura.numero_secuencial}'


class LibroVentas(models.Model):
    anio = models.PositiveIntegerField()
    mes = models.PositiveSmallIntegerField()
    total_ventas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cerrado = models.BooleanField(default=False)
    generado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Libro de Ventas'
        verbose_name_plural = 'Libros de Ventas'
        unique_together = ('anio', 'mes')
        ordering = ['-anio', '-mes']

    def __str__(self):
        return f'Libro de ventas {self.mes}/{self.anio}'


class ReporteSRI(models.Model):
    libro_ventas = models.OneToOneField(LibroVentas, on_delete=models.CASCADE, related_name='reporte_sri')
    archivo = models.FileField(upload_to='reportes_sri/%Y/', null=True, blank=True)
    generado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Reporte SRI'
        verbose_name_plural = 'Reportes SRI'

    def __str__(self):
        return f'Reporte SRI {self.libro_ventas}'
