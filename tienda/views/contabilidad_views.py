from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from tienda.models import Factura, LibroVentas, NotaCredito, Notificacion, ReporteSRI, RetencionImpuesto
from tienda.permissions import EsAdministradorOContador
from tienda.serializers.contabilidad_serializers import (
    CerrarLibroVentasSerializer,
    FacturaSerializer,
    LibroVentasSerializer,
    NotaCreditoSerializer,
    NotificacionSerializer,
    ReporteSRISerializer,
    RetencionImpuestoSerializer,
)
from tienda.services.contabilidad_service import cerrar_libro_ventas_mensual


class FacturaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Factura.objects.select_related('pedido').all()
    serializer_class = FacturaSerializer
    permission_classes = [EsAdministradorOContador]
    filterset_fields = ['estado']
    search_fields = ['numero_secuencial']


class NotaCreditoViewSet(viewsets.ModelViewSet):
    queryset = NotaCredito.objects.all()
    serializer_class = NotaCreditoSerializer
    permission_classes = [EsAdministradorOContador]


class RetencionImpuestoViewSet(viewsets.ModelViewSet):
    queryset = RetencionImpuesto.objects.all()
    serializer_class = RetencionImpuestoSerializer
    permission_classes = [EsAdministradorOContador]


class LibroVentasViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LibroVentas.objects.all()
    serializer_class = LibroVentasSerializer
    permission_classes = [EsAdministradorOContador]

    @action(detail=False, methods=['post'], permission_classes=[EsAdministradorOContador])
    def cerrar(self, request):
        """Puede automatizarse por cron; se deja también accesible manualmente."""
        serializer = CerrarLibroVentasSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reporte = cerrar_libro_ventas_mensual(**serializer.validated_data)
        return Response(ReporteSRISerializer(reporte).data, status=201)


class ReporteSRIViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReporteSRI.objects.select_related('libro_ventas').all()
    serializer_class = ReporteSRISerializer
    permission_classes = [EsAdministradorOContador]


class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user)

    @action(detail=True, methods=['patch'])
    def marcar_leida(self, request, pk=None):
        notificacion = self.get_object()
        notificacion.leida = True
        notificacion.save(update_fields=['leida'])
        return Response(NotificacionSerializer(notificacion).data)
