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
        """MÃ³dulo de Vendedores: resumen detallado de ventas y comisiones acumuladas."""
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
            message='Resumen de vendedor obtenido con Ã©xito.',
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
            return error_response(message='Vendedor no vÃ¡lido.', status=400)

        liquidacion = generar_liquidacion_mensual(vendedor, datos['anio'], datos['mes'])
        return success_response(
            data=LiquidacionMensualSerializer(liquidacion).data,
            message='LiquidaciÃ³n mensual generada correctamente.',
            status=201,
        )

    @action(detail=True, methods=['post'], permission_classes=[EsContador], url_path='marcar-pagada')
    def marcar_pagada(self, request, pk=None):
        """Ãšnica acciÃ³n del contador para pagos: marcar una liquidaciÃ³n como pagada."""
        liquidacion = self.get_object()
        serializer = MarcarPagadaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        liquidacion = marcar_liquidacion_pagada(liquidacion, request.user, serializer.validated_data['comprobante_pago'])
        return success_response(
            data=LiquidacionMensualSerializer(liquidacion).data,
            message='LiquidaciÃ³n marcada como pagada correctamente.',
        )


    @action(detail=False, methods=['get'], permission_classes=[EsAdministradorOContador], url_path='resumen-global')
    def resumen_global(self, request):
        """
        Devuelve TODOS los vendedores con su total de comisiones del mes actual
        y el historico. Genera automaticamente la liquidacion del mes si no existe
        y hay comisiones pendientes.
        """
        from django.utils import timezone
        from django.db.models import Sum
        from tienda.models import ComisionVenta, EstadoComision, LiquidacionMensual
        from tienda.services.comision_service import generar_liquidacion_mensual

        now = timezone.localtime()
        anio = now.year
        mes = now.month

        vendedores = Usuario.objects.filter(
            rol=Rol.VENDEDOR,
            perfil_vendedor__isnull=False,
        ).select_related('perfil_vendedor')

        resultado = []
        for v in vendedores:
            # Comisiones del mes actual pendientes (aun no liquidadas)
            comisiones_mes = ComisionVenta.objects.filter(
                vendedor=v,
                generada_en__year=anio,
                generada_en__month=mes,
            )
            total_pares_mes = comisiones_mes.aggregate(t=Sum('cantidad_pares'))['t'] or 0
            total_monto_mes = comisiones_mes.aggregate(t=Sum('monto'))['t'] or Decimal('0')

            # Obtener o auto-generar liquidacion del mes
            liq = LiquidacionMensual.objects.filter(vendedor=v, periodo_anio=anio, periodo_mes=mes).first()
            if not liq and total_pares_mes > 0:
                liq = generar_liquidacion_mensual(v, anio, mes)

            # Historico total de comisiones de todos los tiempos
            total_historico = ComisionVenta.objects.filter(vendedor=v).aggregate(t=Sum('monto'))['t'] or Decimal('0')

            nombre_parts = [
                v.primer_nombre or getattr(v, 'first_name', '') or '',
                v.primer_apellido or getattr(v, 'last_name', '') or '',
            ]
            nombre = ' '.join(p for p in nombre_parts if p).strip() or v.username

            comp_url = None
            if liq and liq.comprobante_pago:
                try:
                    request_obj = request
                    comp_url = request_obj.build_absolute_uri(liq.comprobante_pago.url)
                except Exception:
                    comp_url = str(liq.comprobante_pago)

            resultado.append({
                'vendedor_id': v.id,
                'vendedor_nombre': nombre,
                'vendedor_email': v.email or '',
                'total_pares_mes': total_pares_mes if not liq else (liq.total_pares or total_pares_mes),
                'total_comisiones_mes': float(total_monto_mes if not liq else (liq.total_comisiones or total_monto_mes)),
                'total_comisiones_historico': float(total_historico),
                'liquidacion_id': liq.id if liq else None,
                'liquidacion_pagada': liq.pagada if liq else False,
                'fecha_pago': liq.fecha_pago.isoformat() if liq and liq.fecha_pago else None,
                'comprobante_pago_url': comp_url,
            })

        return success_response(data=resultado, message='Resumen global de vendedores obtenido.')

    @action(detail=True, methods=['post'], permission_classes=[EsAdministradorOContador], url_path='auto-generar')
    def auto_generar(self, request, pk=None):
        """Auto-genera la liquidacion del mes actual para un vendedor especifico."""
        from django.utils import timezone
        from tienda.services.comision_service import generar_liquidacion_mensual

        vendedor = Usuario.objects.filter(pk=pk, rol=Rol.VENDEDOR).first()
        if not vendedor:
            return error_response(message='Vendedor no valido.', status=400)

        now = timezone.localtime()
        liq = generar_liquidacion_mensual(vendedor, now.year, now.month)
        return success_response(
            data=LiquidacionMensualSerializer(liq).data,
            message='Liquidacion generada automaticamente.',
            status=201,
        )

    @action(detail=False, methods=['get'], permission_classes=[EsAdministradorOContador], url_path='pdf')
    def pdf(self, request):
        """PDF con todos los vendedores y sus pagos del periodo solicitado (?anio=&mes=)."""
        try:
            anio = int(request.query_params.get('anio'))
            mes = int(request.query_params.get('mes'))
        except (TypeError, ValueError):
            return error_response(message='ParÃ¡metros anio y mes son requeridos y deben ser numÃ©ricos.', status=400)

        buffer = generar_pdf_liquidaciones(anio, mes)
        return FileResponse(buffer, as_attachment=True, filename=f'liquidaciones_{mes:02d}_{anio}.pdf')

