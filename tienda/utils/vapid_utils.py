import base64
import os
from pathlib import Path
from django.conf import settings
from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid

PRIVATE_KEY_PATH = settings.BASE_DIR / 'private_key.pem'


def obtener_o_generar_llaves_vapid():
    """
    Obtiene las llaves VAPID configuradas en settings / .env.
    Si no existen, las genera automáticamente y las persiste en private_key.pem.
    Retorna una tupla: (public_key_b64, private_key_pem_path_o_str, claim_email)
    """
    public_key = getattr(settings, 'VAPID_PUBLIC_KEY', None) or os.environ.get('VAPID_PUBLIC_KEY')
    private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None) or os.environ.get('VAPID_PRIVATE_KEY')
    claim_email = getattr(settings, 'VAPID_CLAIM_EMAIL', None) or os.environ.get('VAPID_CLAIM_EMAIL', 'mailto:contacto@dripdiamond.store')

    if not claim_email.startswith('mailto:'):
        claim_email = f'mailto:{claim_email}'

    if public_key and private_key:
        return public_key, private_key, claim_email

    # Si ya existe el archivo private_key.pem
    if PRIVATE_KEY_PATH.exists():
        try:
            v = Vapid.from_file(str(PRIVATE_KEY_PATH))
            pub_bytes = v.public_key.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
            )
            public_key_b64 = base64.urlsafe_b64encode(pub_bytes).decode('utf-8').rstrip('=')
            return public_key_b64, str(PRIVATE_KEY_PATH), claim_email
        except Exception:
            pass

    # Generar un nuevo par de llaves VAPID en private_key.pem
    v = Vapid()
    v.generate_keys()
    v.save_key(str(PRIVATE_KEY_PATH))

    pub_bytes = v.public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    public_key_b64 = base64.urlsafe_b64encode(pub_bytes).decode('utf-8').rstrip('=')

    return public_key_b64, str(PRIVATE_KEY_PATH), claim_email
