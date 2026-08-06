from rest_framework import status
from rest_framework.views import exception_handler

from core.responses import error_response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return error_response(
            message='Error interno del servidor.',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    data = response.data
    if isinstance(data, dict) and data.get('detail') is not None:
        detail = data.pop('detail')
        message = detail[0] if isinstance(detail, list) and detail else str(detail)
    else:
        message = 'Error de validación.' if response.status_code == status.HTTP_400_BAD_REQUEST else 'Ocurrió un error.'

    errors = data if isinstance(data, dict) else None
    return error_response(message=message, errors=errors, status_code=response.status_code)
