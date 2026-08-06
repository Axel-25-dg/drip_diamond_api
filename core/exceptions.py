"""
Manejador global de excepciones para mantener respuestas uniformes en toda la API REST.
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        errors = response.data
        message = "Error de validación o procesamiento."

        if isinstance(errors, dict) and "detail" in errors:
            message = str(errors["detail"])
            errors = {}
        elif isinstance(errors, list) and len(errors) == 1 and isinstance(errors[0], str):
            message = errors[0]
            errors = {}

        response.data = {
            "success": False,
            "message": message,
            "errors": errors,
        }
        return response

    logger.error("Unhandled exception caught in DRF: %s", str(exc), exc_info=True)
    return Response(
        {
            "success": False,
            "message": "Error interno del servidor.",
            "errors": {"detail": str(exc)},
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
