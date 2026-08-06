from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from core.responses import error_response, success_response
from tienda.models import CampanaEmail, EstadoCampana, SegmentoCampana
from tienda.permissions import EsAdministrador
from tienda.serializers.campana_serializers import (
    CampanaEmailListSerializer,
    CampanaEmailSerializer,
)
from tienda.services.campana_service import enviar_campana


class CampanaEmailViewSet(viewsets.ModelViewSet):
    """
    CRUD de campañas de correo masivo + acción para enviar.

    Solo el Administrador puede crear, editar y enviar campañas.
    """
    permission_classes = [IsAuthenticated, EsAdministrador]
    filterset_fields = ['estado', 'segmento']

    def get_queryset(self):
        return CampanaEmail.objects.select_related('creada_por').order_by('-creada_en')

    def get_serializer_class(self):
        if self.action == 'list':
            return CampanaEmailListSerializer
        return CampanaEmailSerializer

    def perform_create(self, serializer):
        serializer.save(creada_por=self.request.user, estado=EstadoCampana.BORRADOR)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message='Campañas obtenidas correctamente.')

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response(data=self.get_serializer(instance).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return success_response(
            data=serializer.data,
            message='Campaña creada en estado BORRADOR. Usa /enviar/ para despacharla.',
            status=201,
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.estado == EstadoCampana.ENVIADO:
            return error_response(
                message='No se puede editar una campaña que ya fue enviada.', status=400
            )
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return success_response(data=serializer.data, message='Campaña actualizada correctamente.')

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.estado == EstadoCampana.ENVIANDO:
            return error_response(
                message='No se puede eliminar una campaña que está siendo enviada.', status=400
            )
        instance.delete()
        return success_response(message='Campaña eliminada correctamente.')

    @action(detail=True, methods=['post'], url_path='enviar')
    def enviar(self, request, pk=None):
        """
        Envía la campaña masiva de inmediato al segmento seleccionado.
        
        Estados permitidos: BORRADOR o FALLIDO.
        El envío actualiza los contadores: total_destinatarios, total_enviados, total_fallidos.
        """
        campana = self.get_object()

        if campana.estado not in (EstadoCampana.BORRADOR, EstadoCampana.FALLIDO):
            return error_response(
                message=f'No se puede enviar una campaña en estado {campana.get_estado_display()}.',
                status=400,
            )

        resultado = enviar_campana(campana.id)

        if 'error' in resultado:
            return error_response(message=resultado['error'], status=400)

        return success_response(
            data=resultado,
            message=(
                f'Campaña enviada: {resultado["enviados"]} correos enviados, '
                f'{resultado["fallidos"]} fallidos de {resultado["total_destinatarios"]} destinatarios.'
            ),
        )

    @action(detail=False, methods=['get'], url_path='segmentos')
    def segmentos(self, request):
        """Lista los segmentos disponibles con su etiqueta."""
        return success_response(
            data=[{'valor': v, 'etiqueta': l} for v, l in SegmentoCampana.choices],
            message='Segmentos disponibles.',
        )
