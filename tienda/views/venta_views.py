from decimal import Decimal
from django.db.models import Sum
from django.http import FileResponse
from rest_framework import permissions, viewsets
from rest_framework.decorators import action

from core.responses import error_response, success_response
from tienda.models import ComisionVenta, EstadoComision, EstadoPedido, LiquidacionMensual, Pedido, Rol, Usuario
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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response(data=self.get_serializer(instance).data)

    @action(detail=False, methods=['get'], url_path='resumen-vendedor')
    def resumen_vendedor(self, request):
        """Módulo de Vendedores: resumen detallado de ventas y comisiones acumuladas."""
        user = request.user
        if not (user.es_vendedor or user.es_administrador):
            return error_response(message='Solo vendedores o administradores pueden acceder a este resumen.', status=403)

        vendedor_target = user
        if user.es_administrador and 'vendedor_id' in request.query_params:
            vendedor_target = Usuario.objects.filter(pk=request.query_params['vendedor_id'], rol=Rol.VENDEDOR).first()
            if not vendedor_target:
                return error_response(message='Vendedor no encontrado.', status=404)

        pedidos_qs = Pedido.objects.filter(vendedor=vendedor_target)
        comisiones_qs = ComisionVenta.objects.filter(vendedor=vendedor_target)

        ventas_asignadas = pedidos_qs.count()
        ventas_pendientes = pedidos_qs.filter(
            estado__in=[EstadoPedido.PENDIENTE_DE_PAGO, EstadoPedido.COMPROBANTE_ENVIADO, EstadoPedido.PAGO_EN_REVISION]
        ).count()
        ventas_pagadas = pedidos_qs.filter(estado=EstadoPedido.PAGO_APROBADO).count()
        ventas_entregadas = pedidos_qs.filter(estado=EstadoPedido.ENTREGADO).count()

        total_vendido = pedidos_qs.filter(estado=EstadoPedido.ENTREGADO).aggregate(Sum('total'))['total__sum'] or Decimal('0.00')
        total_comisiones = comisiones_qs.aggregate(Sum('monto'))['monto__sum'] or Decimal('0.00')
        comisiones_pendientes = comisiones_qs.filter(estado=EstadoComision.PENDIENTE).aggregate(Sum('monto'))['monto__sum'] or Decimal('0.00')
        comisiones_pagadas = comisiones_qs.filter(estado=EstadoComision.LIQUIDADA).aggregate(Sum('monto'))['monto__sum'] or Decimal('0.00')

        return success_response(
            data={
                'vendedor_id': vendedor_target.id,
                'vendedor_nombre': vendedor_target.nombre_completo,
                'ventas_asignadas': ventas_asignadas,
                'ventas_pendientes': ventas_pendientes,
                'ventas_pagadas': ventas_pagadas,
                'ventas_entregadas': ventas_entregadas,
                'total_vendido': float(total_vendido),
                'total_comisiones': float(total_comisiones),
                'comisiones_pendientes': float(comisiones_pendientes),
                'comisiones_pagadas': float(comisiones_pagadas),
            },
            message='Resumen de vendedor obtenido con éxito.',
        )


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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response(data=self.get_serializer(instance).data)

    @action(detail=False, methods=['post'], permission_classes=[EsAdministradorOContador])
    def generar(self, request):
        serializer = GenerarLiquidacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        vendedor = Usuario.objects.filter(pk=datos['vendedor_id'], rol=Rol.VENDEDOR).first()
        if not vendedor:
            return error_response(message='Vendedor no válido.', status=400)

        liquidacion = generar_liquidacion_mensual(vendedor, datos['anio'], datos['mes'])
        return success_response(
            data=LiquidacionMensualSerializer(liquidacion).data,
            message='Liquidación mensual generada correctamente.',
            status=201,
        )

    @action(detail=True, methods=['post'], permission_classes=[EsContador], url_path='marcar-pagada')
    def marcar_pagada(self, request, pk=None):
        """Única acción del contador para pagos: marcar una liquidación como pagada."""
        liquidacion = self.get_object()
        serializer = MarcarPagadaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        liquidacion = marcar_liquidacion_pagada(liquidacion, request.user, serializer.validated_data['comprobante_pago'])
        return success_response(
            data=LiquidacionMensualSerializer(liquidacion).data,
            message='Liquidación marcada como pagada correctamente.',
        )

    @action(detail=False, methods=['get'], permission_classes=[EsAdministradorOContador], url_path='pdf')
    def pdf(self, request):
        """PDF con todos los vendedores y sus pagos del periodo solicitado (?anio=&mes=)."""
        try:
            anio = int(request.query_params.get('anio'))
            mes = int(request.query_params.get('mes'))
        except (TypeError, ValueError):
            return error_response(message='Parámetros anio y mes son requeridos y deben ser numéricos.', status=400)

        buffer = generar_pdf_liquidaciones(anio, mes)
        return FileResponse(buffer, as_attachment=True, filename=f'liquidaciones_{mes:02d}_{anio}.pdf')
