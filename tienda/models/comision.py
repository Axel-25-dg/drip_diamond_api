from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class EstadoComision(models.TextChoices):
    PENDIENTE = 'PENDIENTE', 'Pendiente'
    LIQUIDADA = 'LIQUIDADA', 'Liquidada'


class ComisionVenta(models.Model):
    """
    Se crea ÚNICAMENTE cuando el contador confirma que el cliente ya recibió
    su paquete. Antes de eso NO existe registro de comisión para ese pedido.

    Monto = cantidad total de pares del pedido x settings.COMISION_FIJA_POR_PAR.
    """
    pedido = models.OneToOneField('tienda.Pedido', on_delete=models.PROTECT, related_name='comision')
    vendedor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='comisiones')
    cantidad_pares = models.PositiveIntegerField()
    monto_por_par = models.DecimalField(max_digits=6, decimal_places=2)
    monto = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    estado = models.CharField(max_length=15, choices=EstadoComision.choices, default=EstadoComision.PENDIENTE)
    liquidacion = models.ForeignKey(
        'tienda.LiquidacionMensual', on_delete=models.SET_NULL, null=True, blank=True, related_name='comisiones'
    )

    confirmada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='entregas_confirmadas',
        help_text='Contador que confirmó la entrega y disparó esta comisión',
    )
    generada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comisión de Venta'
        verbose_name_plural = 'Comisiones de Venta'
        indexes = [models.Index(fields=['vendedor', 'estado'])]

    def __str__(self):
        return f'Comisión ${self.monto} — {self.vendedor} (pedido #{self.pedido_id})'


class LiquidacionMensual(models.Model):
    """
    Cierre mensual de comisiones de un vendedor. El administrador transfiere
    y sube el comprobante; el CONTADOR es quien marca "pagada" (es una de
    sus dos únicas acciones manuales).
    """
    vendedor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='liquidaciones')
    periodo_anio = models.PositiveIntegerField()
    periodo_mes = models.PositiveSmallIntegerField()
    total_pares = models.PositiveIntegerField(default=0)
    total_comisiones = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pagada = models.BooleanField(default=False)
    marcada_pagada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='liquidaciones_marcadas', limit_choices_to={'rol': 'CONTADOR'},
    )
    fecha_pago = models.DateTimeField(null=True, blank=True)
    comprobante_pago = models.FileField(upload_to='comprobantes_comision/%Y/%m/', null=True, blank=True)

    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Liquidación Mensual'
        verbose_name_plural = 'Liquidaciones Mensuales'
        unique_together = ('vendedor', 'periodo_anio', 'periodo_mes')
        ordering = ['-periodo_anio', '-periodo_mes']

    def __str__(self):
        return f'Liquidación {self.periodo_mes}/{self.periodo_anio} — {self.vendedor}'
