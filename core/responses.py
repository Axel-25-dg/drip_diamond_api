from typing import Any, Dict, Optional

from rest_framework import status
from rest_framework.response import Response


def success_response(
    data: Any = None,
    message: str = 'Operación realizada correctamente.',
    status_code: int = status.HTTP_200_OK,
) -> Response:
    return Response(
        {
            'success': True,
            'message': message,
            'data': data if data is not None else {},
        },
        status=status_code,
    )


def paginated_response(
    results: Any,
    count: int,
    page: int,
    page_size: int,
    message: str = 'Operación realizada correctamente.',
    status_code: int = status.HTTP_200_OK,
) -> Response:
    return Response(
        {
            'success': True,
            'message': message,
            'data': results,
            'pagination': {
                'count': count,
                'page': page,
                'page_size': page_size,
            },
        },
        status=status_code,
    )


def error_response(
    message: str = 'Ocurrió un error.',
    errors: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    payload = {
        'success': False,
        'message': message,
        'errors': errors or {},
    }
    return Response(payload, status=status_code)
