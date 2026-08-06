import uuid

from django.conf import settings
from django.db import models


class PerfilVendedor(models.Model):
    """
    Vendedor: gana una comisión FIJA por par vendido (settings.COMISION_FIJA_POR_PAR),
    no un porcentaje. El cliente debe elegir su código para que la venta le cuente.
    """
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil_vendedor')
    codigo_vendedor = models.CharField(max_length=12, unique=True, editable=False)
    activo = models.BooleanField(default=True)

    banco = models.CharField(max_length=100, blank=True)
    tipo_cuenta = models.CharField(max_length=20, blank=True)
    numero_cuenta = models.CharField(max_length=30, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil de Vendedor'
        verbose_name_plural = 'Perfiles de Vendedor'

    def save(self, *args, **kwargs):
        if not self.codigo_vendedor:
            self.codigo_vendedor = f'VEN-{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.codigo_vendedor} — {self.usuario}'


class PerfilContador(models.Model):
    """
    El contador solo confirma entregas (para que se sume la comisión) y marca
    liquidaciones como pagadas. Todo lo demás de su función es automático.
    """
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil_contador')
    numero_autorizacion_sri = models.CharField(max_length=50, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Perfil de Contador'
        verbose_name_plural = 'Perfiles de Contador'

    def __str__(self):
        return f'Contador: {self.usuario}'
