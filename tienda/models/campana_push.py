from django.conf import settings
from django.db import models


class SegmentoPush(models.TextChoices):
    TODOS = 'TODOS', 'Todos los dispositivos suscritos'
    CLIENTES = 'CLIENTES', 'Solo Clientes'
    VENDEDORES = 'VENDEDORES', 'Solo Vendedores'
    ESPECIFICOS = 'ESPECIFICOS', 'Usuarios específicos seleccionados'


class CampanaNotificacionPush(models.Model):
    """
    Registra las notificaciones masivas o personalizadas enviadas por los Administradores
    a las barras de sistema de los usuarios.
    """
    titulo = models.CharField(max_length=120, help_text='Título llamativo de la notificación')
    cuerpo = models.TextField(max_length=500, help_text='Mensaje principal de la notificación')
    icono_url = models.URLField(max_length=500, blank=True, default='', help_text='URL del icono (ej. logo o zapatilla)')
    imagen_url = models.URLField(max_length=500, blank=True, default='', help_text='Banner o foto grande desplegable')
    url_destino = models.CharField(max_length=300, default='/', help_text='Ruta o URL que se abrirá al dar clic')
    badge_url = models.URLField(max_length=500, blank=True, default='', help_text='Insignia pequeña de la barra')
    sonido_activo = models.BooleanField(default=True, help_text='Reprodur sonido de notificación')
    vibracion_activa = models.BooleanField(default=True, help_text='Vibrar en teléfonos móviles')

    segmento = models.CharField(max_length=20, choices=SegmentoPush.choices, default=SegmentoPush.TODOS)
    usuarios_especificos = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='campanas_push_recibidas',
        help_text='Aplica si el segmento es Usuarios Específicos'
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campanas_push_creadas'
    )
    total_enviados = models.IntegerField(default=0)
    total_exitosos = models.IntegerField(default=0)
    total_fallidos = models.IntegerField(default=0)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Campaña Push Personalizada'
        verbose_name_plural = 'Campañas Push Personalizadas'
        ordering = ['-creada_en']

    def __str__(self):
        return f'{self.titulo} ({self.get_segmento_display()}) - {self.creada_en.strftime("%Y-%m-%d %H:%M")}'
