import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class ResendError(Exception):
    pass


@dataclass
class EmailMessage:
    subject: str
    html_template: str
    context: Dict[str, Any]
    recipients: Iterable[str]
    text_template: Optional[str] = None
    from_email: Optional[str] = None


def send_templated_email(message: EmailMessage) -> Dict[str, Any]:
    if not settings.RESEND_API_KEY:
        raise ResendError('La clave de Resend no está configurada.')

    html_content = render_to_string(message.html_template, message.context)
    text_content = (
        render_to_string(message.text_template, message.context)
        if message.text_template
        else strip_tags(html_content)
    )

    payload = {
        'from': message.from_email or settings.DEFAULT_FROM_EMAIL,
        'to': list(message.recipients),
        'subject': message.subject,
        'html': html_content,
        'text': text_content,
    }

    headers = {'Authorization': f'Bearer {settings.RESEND_API_KEY}', 'Content-Type': 'application/json'}
    response = requests.post('https://api.resend.com/emails', json=payload, headers=headers, timeout=15)
    if not response.ok:
        logger.exception('Error enviando correo con Resend: %s', response.text)
        raise ResendError('No se pudo enviar el correo electrónico.')

    return response.json()
