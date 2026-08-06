from django.conf import settings
from django.db import models


class SesionUsuario(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sesiones')
    ip = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255, blank=True)
    iniciada_en = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Sesión de Usuario'
        verbose_name_plural = 'Sesiones de Usuario'
        ordering = ['-iniciada_en']

    def __str__(self):
        return f'{self.usuario} desde {self.ip} ({self.iniciada_en:%Y-%m-%d %H:%M})'


class IntentoLogin(models.Model):
    username_intentado = models.CharField(max_length=150, blank=True)
    ip = models.GenericIPAddressField()
    exitoso = models.BooleanField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Intento de Login'
        verbose_name_plural = 'Intentos de Login'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['ip', 'fecha']),
            models.Index(fields=['username_intentado', 'fecha']),
        ]

    def __str__(self):
        estado = 'exitoso' if self.exitoso else 'fallido'
        return f'{self.username_intentado} desde {self.ip} — {estado}'


class IPBloqueada(models.Model):
    ip = models.GenericIPAddressField(unique=True)
    motivo = models.CharField(max_length=255, default='Múltiples intentos fallidos de login')
    bloqueada_en = models.DateTimeField(auto_now_add=True)
    desbloquear_en = models.DateTimeField()

    class Meta:
        verbose_name = 'IP Bloqueada'
        verbose_name_plural = 'IPs Bloqueadas'

    def __str__(self):
        return f'{self.ip} bloqueada hasta {self.desbloquear_en:%Y-%m-%d %H:%M}'


class LogAuditoria(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='acciones_auditadas'
    )
    accion = models.CharField(max_length=100)
    modelo_afectado = models.CharField(max_length=100, blank=True)
    objeto_id = models.CharField(max_length=50, blank=True)
    detalle = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        ordering = ['-fecha']
        indexes = [models.Index(fields=['modelo_afectado', 'objeto_id'])]

    def __str__(self):
        return f'{self.usuario} — {self.accion} ({self.fecha:%Y-%m-%d %H:%M})'
