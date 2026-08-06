"""
Integración con Google Maps Geocoding API. Se usa SOLO en el checkout para
convertir la dirección que escribe/autocompleta el cliente en coordenadas
exactas (lat/lng) + dirección formateada, y así guardarlas en
DireccionEnvioPedido. Requiere settings.GOOGLE_MAPS_API_KEY.
"""
import requests
from django.conf import settings


class GoogleMapsError(Exception):
    pass


def geocodificar_direccion(direccion_texto: str, ciudad: str = '') -> dict:
    """
    Devuelve {direccion_formateada, latitud, longitud, place_id}.
    Si no hay API key configurada, lanza GoogleMapsError para que la vista
    le pida al frontend que use el modo manual (lat/lng ya resueltos por
    el widget de Places Autocomplete del propio frontend).
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        raise GoogleMapsError(
            'No hay GOOGLE_MAPS_API_KEY configurada. Envía latitud/longitud '
            'ya resueltas desde el Autocomplete del frontend en su lugar.'
        )

    consulta = f'{direccion_texto}, {ciudad}' if ciudad else direccion_texto
    respuesta = requests.get(
        settings.GOOGLE_MAPS_GEOCODE_URL,
        params={'address': consulta, 'key': settings.GOOGLE_MAPS_API_KEY, 'region': 'ec'},
        timeout=8,
    )
    datos = respuesta.json()

    if datos.get('status') != 'OK' or not datos.get('results'):
        raise GoogleMapsError(f'No se pudo geocodificar la dirección (status: {datos.get("status")}).')

    resultado = datos['results'][0]
    ubicacion = resultado['geometry']['location']

    return {
        'direccion_formateada': resultado['formatted_address'],
        'latitud': ubicacion['lat'],
        'longitud': ubicacion['lng'],
        'place_id': resultado.get('place_id', ''),
    }
