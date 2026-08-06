"""
Envío de correos mediante la API HTTP de Resend (https://resend.com) —
no se usa SMTP en ningún punto del sistema.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

RESEND_API_URL = 'https://api.resend.com/emails'


class ResendError(Exception):
    pass


def enviar_correo_resend(destinatario: str, asunto: str, html: str) -> bool:
    """
    Envía un correo vía Resend. Devuelve True/False según el éxito;
    nunca lanza excepción hacia arriba (para no romper el flujo de negocio
    si el correo falla) — el error queda registrado en logs.
    """
    if not settings.RESEND_API_KEY:
        logger.warning('RESEND_API_KEY no configurada — correo NO enviado a %s: %s', destinatario, asunto)
        return False

    try:
        respuesta = requests.post(
            RESEND_API_URL,
            headers={
                'Authorization': f'Bearer {settings.RESEND_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'from': settings.DEFAULT_FROM_EMAIL,
                'to': [destinatario],
                'subject': asunto,
                'html': html,
            },
            timeout=10,
        )
        if respuesta.status_code >= 400:
            logger.error('Resend respondió %s al enviar a %s: %s', respuesta.status_code, destinatario, respuesta.text)
            return False
        return True
    except requests.RequestException as exc:
        logger.error('Error de red enviando correo por Resend a %s: %s', destinatario, exc)
        return False
