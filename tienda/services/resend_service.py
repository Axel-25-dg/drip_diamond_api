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
    Envía un correo vía SMTP (Gmail) si hay credenciales configuradas en .env,
    o mediante la API HTTP de Resend en su defecto.
    Devuelve True/False según el éxito y no rompe la ejecución si el envío falla.
    """
    # 1. Prioridad: SMTP (ej. Gmail con Contraseña de Aplicación)
    if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
        try:
            from django.core.mail import EmailMultiAlternatives
            remitente = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
            msg = EmailMultiAlternatives(
                subject=asunto,
                body='',
                from_email=remitente,
                to=[destinatario],
            )
            msg.attach_alternative(html, "text/html")
            msg.send(fail_silently=False)
            return True
        except Exception as exc:
            logger.error('Error enviando correo vía SMTP a %s: %s', destinatario, exc)
            return False

    # 2. Fallback: API HTTP de Resend
    if not settings.RESEND_API_KEY:
        logger.warning('Ni SMTP ni RESEND_API_KEY configurados — correo NO enviado a %s: %s', destinatario, asunto)
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

