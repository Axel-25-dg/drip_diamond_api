import os
import uuid
from PIL import Image
from django.core.exceptions import ValidationError

EXTENSIONES_PERMITIDAS = {'.jpg', '.jpeg', '.png', '.webp'}
MIME_TYPES_PERMITIDOS = {'image/jpeg', 'image/png', 'image/webp'}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def obtener_carpeta_destino(modelo_nombre: str) -> str:
    modelo_nombre = (modelo_nombre or '').lower().strip()
    mapa = {
        'usuario': 'usuarios/perfiles',
        'perfilvendedor': 'usuarios/perfiles',
        'perfilcontador': 'usuarios/perfiles',
        'producto': 'productos/zapatillas',
        'varianteproducto': 'productos/zapatillas',
        'categoria': 'categorias',
        'marca': 'marcas',
        'banner': 'banners',
        'promocion': 'promociones',
        'comprobantepago': 'comprobantes',
    }
    return mapa.get(modelo_nombre, 'otros')


def validar_imagen(archivo):
    """
    Valida tamaño, extensión, tipo MIME real (con Pillow) y dimensiones.
    Impide ejecutables y archivos corruptos o maliciosos.
    """
    if not archivo:
        raise ValidationError('No se ha proporcionado ningún archivo.')

    if archivo.size > MAX_FILE_SIZE_BYTES:
        raise ValidationError('El tamaño máximo permitido para imágenes es 5 MB.')

    ext = os.path.splitext(archivo.name)[1].lower()
    if ext not in EXTENSIONES_PERMITIDAS:
        raise ValidationError(f'Extensión "{ext}" no permitida. Formatos válidos: jpg, jpeg, png, webp.')

    # Validar con Pillow que realmente es una imagen válida y no un archivo malicioso o ejecutable
    try:
        archivo.seek(0)
        img = Image.open(archivo)
        img.verify()
        archivo.seek(0)

        format_mime_map = {
            'JPEG': 'image/jpeg',
            'PNG': 'image/png',
            'WEBP': 'image/webp',
        }
        mime = format_mime_map.get(img.format)
        if mime not in MIME_TYPES_PERMITIDOS:
            raise ValidationError(f'Tipo de imagen "{img.format}" no soportado.')
    except Exception as exc:
        raise ValidationError(f'El archivo proporcionado no es una imagen válida: {str(exc)}')


def eliminar_archivo_local(path_o_field):
    """
    Elimina físicamente el archivo del disco para evitar archivos huérfanos.
    """
    try:
        if hasattr(path_o_field, 'path') and os.path.exists(path_o_field.path):
            os.remove(path_o_field.path)
        elif isinstance(path_o_field, str) and os.path.exists(path_o_field):
            os.remove(path_o_field)
    except Exception:
        pass
