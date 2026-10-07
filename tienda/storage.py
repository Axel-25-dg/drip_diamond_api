import io
import mimetypes
import os
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseStorage(Storage):
    """
    Almacenamiento de archivos e imágenes persistente en Base de Datos (PostgreSQL / SQLite).
    Diseñado para Vercel y entornos Serverless:
    - 0 dependencias de almacenamiento de terceros (sin Cloudinary, AWS S3, etc.).
    - Comprime automáticamente las imágenes a WebP optimizado (máx 1200px, 82% calidad),
      reduciendo el tamaño a ~40-100 KB para no sobrecargar la base de datos.
    - Sirve las imágenes vía URLs cacheadas por CDN (/api/media/...).
    """

    def _get_model(self):
        from tienda.models.archivo_db import ArchivoAlmacenado
        return ArchivoAlmacenado

    def _optimizar_imagen(self, content, nombre):
        """
        Comprime y redimensiona la imagen usando Pillow para que ocupe el mínimo espacio posible.
        """
        try:
            content.seek(0)
            img = Image.open(content)
            img = ImageOps.exif_transpose(img)

            # Redimensionar si es muy grande manteniendo proporción
            max_size = (1200, 1200)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            # Convertir a WebP para máxima compresión y compatibilidad moderna
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img.save(buffer, format='WEBP', quality=82, method=6)
            else:
                img = img.convert('RGB')
                img.save(buffer, format='WEBP', quality=82, method=6)

            buffer.seek(0)
            nombre_base = os.path.splitext(nombre)[0] + '.webp'
            return buffer.getvalue(), 'image/webp', nombre_base
        except Exception:
            # Si no es procesable con Pillow (ej. svg, pdf u otro archivo), guardar los bytes originales
            content.seek(0)
            raw_data = content.read()
            mime = mimetypes.guess_type(nombre)[0] or 'application/octet-stream'
            return raw_data, mime, nombre

    def _save(self, name, content):
        name = name.replace('\\', '/').lstrip('/')
        data, content_type, nombre_optimizado = self._optimizar_imagen(content, name)

        ArchivoAlmacenado = self._get_model()
        ArchivoAlmacenado.objects.update_or_create(
            nombre=nombre_optimizado,
            defaults={
                'datos': data,
                'content_type': content_type,
                'tamano_bytes': len(data),
            }
        )
        return nombre_optimizado

    def _open(self, name, mode='rb'):
        name = name.replace('\\', '/').lstrip('/')
        ArchivoAlmacenado = self._get_model()
        archivo = ArchivoAlmacenado.objects.filter(nombre=name).first()
        if archivo:
            return ContentFile(bytes(archivo.datos), name=name)
        raise FileNotFoundError(f"Archivo no encontrado en base de datos: {name}")

    def exists(self, name):
        name = name.replace('\\', '/').lstrip('/')
        ArchivoAlmacenado = self._get_model()
        return ArchivoAlmacenado.objects.filter(nombre=name).exists()

    def delete(self, name):
        name = name.replace('\\', '/').lstrip('/')
        ArchivoAlmacenado = self._get_model()
        ArchivoAlmacenado.objects.filter(nombre=name).delete()

    def url(self, name):
        name = name.replace('\\', '/').lstrip('/')
        return f'/api/media/{name}'

    def size(self, name):
        name = name.replace('\\', '/').lstrip('/')
        ArchivoAlmacenado = self._get_model()
        archivo = ArchivoAlmacenado.objects.filter(nombre=name).first()
        return archivo.tamano_bytes if archivo else 0
