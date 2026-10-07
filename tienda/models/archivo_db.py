from django.db import models


class ArchivoAlmacenado(models.Model):
    """
    Almacena archivos e imágenes binarias directamente en la base de datos (PostgreSQL/SQLite).
    Permite subida de imágenes 100% persistente y gratuita en entornos Serverless como Vercel
    sin depender de servicios de terceros como Cloudinary o AWS S3.
    """
    nombre = models.CharField(max_length=255, unique=True, db_index=True)
    datos = models.BinaryField()
    content_type = models.CharField(max_length=100, default='image/webp')
    tamano_bytes = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Archivo Almacenado'
        verbose_name_plural = 'Archivos Almacenados'
        ordering = ['-actualizado_en']

    def __str__(self):
        return f'{self.nombre} ({self.tamano_bytes} bytes)'
