import os
import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


def _ruta_imagen(instance, nombre_archivo):
    """
    Organiza las imágenes en carpetas por tipo de modelo, ej:
    media/imagenes/producto/<uuid>.jpg, media/imagenes/marca/<uuid>.png
    Nombre único con UUID para evitar colisiones/sobrescrituras.
    """
    extension = os.path.splitext(nombre_archivo)[1].lower()
    carpeta = instance.content_type.model if instance.content_type_id else 'general'
    return f'imagenes/{carpeta}/{uuid.uuid4().hex}{extension}'


class ImagenAdjunta(models.Model):
    """
    Imagen genérica reutilizable, asociable a CUALQUIER modelo del sistema
    (producto, marca, promoción, etc.) mediante GenericForeignKey, sin
    necesidad de crear un modelo de imagen distinto por cada entidad.
    Almacenamiento local (MEDIA_ROOT/MEDIA_URL) — sin Cloudinary/S3.
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
