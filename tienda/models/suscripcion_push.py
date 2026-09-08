from django.conf import settings
from django.db import models


class SuscripcionPush(models.Model):
    """
    Guarda las suscripciones del navegador/sistema operativo (VAPID Push API W3C)
    para enviar notificaciones nativas a la barra de estado de los dispositivos.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='suscripciones_push',
        null=True,
        blank=True,
        help_text='Usuario asociado a la suscripción. Puede ser nulo para visitantes/invitados.'
    )
    endpoint = models.URLField(max_length=700, unique=True, help_text='URL de endpoint Push generada por el navegador')
    p256dh = models.CharField(max_length=255, help_text='Llave pública cliente p256dh')
    auth = models.CharField(max_length=255, help_text='Secreto de autenticación cliente auth')
    user_agent = models.CharField(max_length=300, blank=True, default='')
    ip_registro = models.GenericIPAddressField(null=True, blank=True)
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    ultima_actividad = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Suscripción Push'
        verbose_name_plural = 'Suscripciones Push'
        ordering = ['-ultima_actividad']

    def __str__(self):
        usr = self.usuario.email if self.usuario else 'Anónimo'
        return f'Push [{usr}] - {self.endpoint[:40]}...'
