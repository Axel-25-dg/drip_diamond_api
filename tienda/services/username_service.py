import re
import unicodedata


def _limpiar(texto: str) -> str:
    """Quita tildes, ñ→n y caracteres no alfanuméricos."""
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^a-zA-Z0-9]', '', texto)
    return texto.lower()


def generar_username(primer_nombre: str, primer_apellido: str) -> str:
    """
    Genera un username base a partir del primer nombre y primer apellido,
    y le agrega un sufijo numérico si ya existe, garantizando unicidad.
    El usuario puede editarlo después (ver serializers) siempre que se
    mantenga único.
    """
    from tienda.models import Usuario

    base = _limpiar(primer_nombre) + '.' + _limpiar(primer_apellido)
    if not base or base == '.':
        base = 'usuario'

    username = base
    contador = 1
    while Usuario.objects.filter(username=username).exists():
        contador += 1
        username = f'{base}{contador}'
    return username


def username_disponible(username: str, usuario_actual_id=None) -> bool:
    from tienda.models import Usuario

    qs = Usuario.objects.filter(username=username)
    if usuario_actual_id:
        qs = qs.exclude(pk=usuario_actual_id)
    return not qs.exists()
