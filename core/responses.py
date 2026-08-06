"""
Módulo core de la aplicación: respuestas estandarizadas y manejo global de excepciones.
"""
from rest_framework.response import Response


def success_response(data=None, message: str = "Operación realizada correctamente.", status: int = 200) -> Response:
    return Response(
        {
            "success": True,
            "message": message,
            "data": data if data is not None else {},
        },
        status=status,
    )


def error_response(message: str = "Error en la solicitud.", errors=None, status: int = 400) -> Response:
    return Response(
        {
            "success": False,
            "message": message,
            "errors": errors if errors is not None else {},
        },
        status=status,
    )
