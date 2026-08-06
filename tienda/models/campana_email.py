from django.conf import settings
from django.db import models


class SegmentoCampana(models.TextChoices):
    TODOS_LOS_CLIENTES = 'TODOS_LOS_CLIENTES', 'Todos los clientes'
    VENDEDORES = 'VENDEDORES', 'Todos los vendedores'
    CONTADORES = 'CONTADORES', 'Todos los contadores'
    CLIENTES_CON_COMPRAS = 'CLIENTES_CON_COMPRAS', 'Clientes con compras registradas'
    CLIENTES_SIN_COMPRAS = 'CLIENTES_SIN_COMPRAS', 'Clientes sin compras registradas'


class EstadoCampana(models.TextChoices):
    BORRADOR = 'BORRADOR', 'Borrador'
    PROGRAMADO = 'PROGRAMADO', 'Programado'
    ENVIANDO = 'ENVIANDO', 'Enviando'
    ENVIADO = 'ENVIADO', 'Enviado'
    FALLIDO = 'FALLIDO', 'Fallido'


class CampanaEmail(models.Model):
    """
    Módulo para campañas de correos masivos.
    Permite guardar historial, reutilizar plantillas HTML, enviar por segmentos
    y programar envíos futuros (preparado para Celery/workers).
    """
    titulo = models.CharField(max_length=150)
    asunto = models.CharField(max_length=200)
    contenido_html = models.TextField(help_text='Contenido HTML o plantilla renderizable')
    segmento = models.CharField(max_length=30, choices=SegmentoCampana.choices, default=SegmentoCampana.TODOS_LOS_CLIENTES)
    
    estado = models.CharField(max_length=20, choices=EstadoCampana.choices, default=EstadoCampana.BORRADOR)
    programado_para = models.DateTimeField(null=True, blank=True)
    
    total_destinatarios = models.PositiveIntegerField(default=0)
    total_enviados = models.PositiveIntegerField(default=0)
    total_fallidos = models.PositiveIntegerField(default=0)

    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='campanas_creadas'
    )
    creada_en = models.DateTimeField(auto_now_add=True)
    enviada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Campaña de Email'
        verbose_name_plural = 'Campañas de Email'
        ordering = ['-creada_en']

    def __str__(self):
        return f'{self.titulo} ({self.get_segmento_display()}) — {self.get_estado_display()}'
