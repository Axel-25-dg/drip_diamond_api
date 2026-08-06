import os
import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


def _ruta_imagen(instance, nombre_archivo):
    """
    Organiza las imágenes en carpetas según su módulo/entidad:
    - media/usuarios/perfiles/
    - media/productos/zapatillas/
    - media/categorias/
    - media/marcas/
    - media/banners/
    - media/promociones/
    - media/comprobantes/
    - media/otros/
    Nombre único con UUID4.
    """
    from tienda.services.imagen_service import obtener_carpeta_destino

    extension = os.path.splitext(nombre_archivo)[1].lower()
    modelo = instance.content_type.model if instance.content_type_id else 'otros'
    subcarpeta = obtener_carpeta_destino(modelo)
    return f'{subcarpeta}/{uuid.uuid4().hex}{extension}'


class ImagenAdjunta(models.Model):
    """
    Imagen genérica reutilizable, asociable a CUALQUIER modelo del sistema
    mediante GenericForeignKey. Almacenamiento local (MEDIA_ROOT/MEDIA_URL).
    """
    archivo = models.ImageField(upload_to=_ruta_imagen)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    orden = models.PositiveSmallIntegerField(default=0)
    es_principal = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imagen'
        verbose_name_plural = 'Imágenes'
        ordering = ['orden', 'creada_en']
        indexes = [models.Index(fields=['content_type', 'object_id'])]

    def __str__(self):
        return f'Imagen #{self.pk} de {self.content_type} #{self.object_id}'
