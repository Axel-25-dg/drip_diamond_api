from django.http import FileResponse
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from tienda.models import ComisionVenta, LiquidacionMensual, Rol, Usuario
from tienda.permissions import EsAdministrador, EsAdministradorOContador, EsContador
from tienda.serializers.venta_serializers import (
    ComisionVentaSerializer,
    GenerarLiquidacionSerializer,
    LiquidacionMensualSerializer,
    MarcarPagadaSerializer,
)
from tienda.services.comision_service import generar_liquidacion_mensual, marcar_liquidacion_pagada
from tienda.services.pdf_service import generar_pdf_liquidaciones


class ComisionVentaViewSet(viewsets.ReadOnlyModelViewSet):
    """Cada vendedor ve solo sus comisiones (ya confirmadas por el contador); Admin/Contador ven todas."""
    serializer_class = ComisionVentaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['estado', 'vendedor']

    def get_queryset(self):
        user = self.request.user
        qs = ComisionVenta.objects.select_related('pedido', 'vendedor')
        if user.es_administrador or user.es_contador:
            return qs
        return qs.filter(vendedor=user)


class LiquidacionMensualViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LiquidacionMensualSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['vendedor', 'pagada', 'periodo_anio', 'periodo_mes']

    def get_queryset(self):
        user = self.request.user
        qs = LiquidacionMensual.objects.select_related('vendedor').prefetch_related('comisiones')
        if user.es_administrador or user.es_contador:
            return qs
        return qs.filter(vendedor=user)

    @action(detail=False, methods=['post'], permission_classes=[EsAdministradorOContador])
    def generar(self, request):
        serializer = GenerarLiquidacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        vendedor = Usuario.objects.filter(pk=datos['vendedor_id'], rol=Rol.VENDEDOR).first()
        if not vendedor:
            return Response({'detail': 'Vendedor no válido.'}, status=400)

        liquidacion = generar_liquidacion_mensual(vendedor, datos['anio'], datos['mes'])
        return Response(LiquidacionMensualSerializer(liquidacion).data, status=201)

    @action(detail=True, methods=['post'], permission_classes=[EsContador], url_path='marcar-pagada')
    def marcar_pagada(self, request, pk=None):
        """Única acción del contador para pagos: marcar una liquidación como pagada."""
        liquidacion = self.get_object()
        serializer = MarcarPagadaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        liquidacion = marcar_liquidacion_pagada(liquidacion, request.user, serializer.validated_data['comprobante_pago'])
        return Response(LiquidacionMensualSerializer(liquidacion).data)

    @action(detail=False, methods=['get'], permission_classes=[EsAdministradorOContador], url_path='pdf')
    def pdf(self, request):
        """PDF con todos los vendedores y sus pagos del periodo solicitado (?anio=&mes=)."""
        anio = int(request.query_params.get('anio'))
        mes = int(request.query_params.get('mes'))
        buffer = generar_pdf_liquidaciones(anio, mes)
        return FileResponse(buffer, as_attachment=True, filename=f'liquidaciones_{mes:02d}_{anio}.pdf')
