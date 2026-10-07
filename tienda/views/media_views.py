import mimetypes
from django.http import HttpResponse, Http404
from tienda.models.archivo_db import ArchivoAlmacenado


def servir_archivo_db(request, ruta):
    """
    Sirve imágenes y archivos almacenados en la base de datos con caché agresivo (CDN / Browser).
    Ruta puede ser 'productos/zapato.webp', 'usuarios/perfiles/foto.webp', etc.
    """
    ruta_limpia = ruta.replace('\\', '/').lstrip('/')
    archivo = ArchivoAlmacenado.objects.filter(nombre__in=[ruta_limpia, f'/{ruta_limpia}']).first()
    if not archivo:
        base, _ = ruta_limpia.rsplit('.', 1) if '.' in ruta_limpia else (ruta_limpia, '')
        if base:
            archivo = ArchivoAlmacenado.objects.filter(nombre__startswith=base).first()

    if not archivo:
        raise Http404("Archivo no encontrado en la base de datos.")

    content_type = archivo.content_type or mimetypes.guess_type(ruta_limpia)[0] or 'application/octet-stream'
    contenido = bytes(archivo.datos)

    response = HttpResponse(contenido, content_type=content_type)
    # Headers de caché para Edge CDN de Vercel y navegador (1 año)
    response['Cache-Control'] = 'public, max-age=31536000, immutable'
    response['Content-Length'] = len(contenido)
    return response
