from typing import Any, Dict

from rest_framework.renderers import JSONRenderer


class UniformJSONRenderer(JSONRenderer):
    media_type = 'application/json'

    def render(self, data: Any, accepted_media_type=None, renderer_context=None):
        if renderer_context is None:
            return super().render(data, accepted_media_type, renderer_context)

        response = renderer_context.get('response')
        if response is None:
            return super().render(data, accepted_media_type, renderer_context)

        if data is None:
            data = {}

        payload: Dict[str, Any]
        if response.status_code >= 400:
            message = ''
            errors = {}
            if isinstance(data, dict):
                if 'detail' in data:
                    detail = data.get('detail')
                    if isinstance(detail, (list, dict)):
                        message = detail[0] if isinstance(detail, list) and detail else str(detail)
                    else:
                        message = str(detail)
                errors = {k: v for k, v in data.items() if k != 'detail'}
            else:
                message = str(data)
            payload = {
                'success': False,
                'message': message or 'Ocurrió un error.',
                'errors': errors,
            }
        elif isinstance(data, dict) and {'success', 'message', 'data'}.issubset(data.keys()):
            payload = data
        elif isinstance(data, dict) and 'results' in data:
            pagination = data.copy()
            results = pagination.pop('results')
            payload = {
                'success': True,
                'message': '',
                'data': results,
                'pagination': pagination,
            }
        else:
            payload = {
                'success': True,
                'message': '',
                'data': data,
            }

        return super().render(payload, accepted_media_type, renderer_context)
