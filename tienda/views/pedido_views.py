from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView

from core.responses import error_response, success_response
from tienda.models import ComprobantePago, Pedido, Rol, Usuario, EstadoPedido
from tienda.permissions import EsAdministrador, EsAdministradorOContador, EsDuenoOAdministrador
from tienda.serializers.pedido_serializers import (
    ComprobantePagoSerializer,
    CrearPedidoSerializer,
    DefinirCostoEnvioSerializer,
    PedidoSerializer,
    VerificarComprobanteSerializer,
)
from tienda.services.envio_service import marcar_pedido_enviado
from tienda.services.imagen_service import validar_imagen
from tienda.services.pedido_service import CarritoVacioError, StockInsuficienteError, crear_pedido_desde_carrito



class PedidoViewSet(viewsets.ModelViewSet):
    serializer_class = PedidoSerializer
    permission_classes = [permissions.IsAuthenticated, EsDuenoOAdministrador]
    http_method_names = ['get', 'post', 'head', 'options']
    filterset_fields = ['estado']

    def get_queryset(self):
        user = self.request.user
        qs = Pedido.objects.select_related('usuario', 'vendedor', 'direccion_envio').prefetch_related('detalles', 'historial')
        if user.es_administrador or user.es_contador:
            return qs
        if user.es_vendedor:
            return qs.filter(vendedor=user)
        return qs.filter(usuario=user)

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
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = CrearPedidoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        vendedor_id = datos.pop('vendedor_id', None)
        vendedor = None
        if vendedor_id:
            vendedor = Usuario.objects.filter(pk=vendedor_id, rol=Rol.VENDEDOR).first()
            if not vendedor:
                return error_response(message='El vendedor seleccionado no es válido.', status=400)

        tipo_entrega = datos.pop('tipo_entrega')
        direccion_data = datos

        try:
            pedido = crear_pedido_desde_carrito(
                usuario=request.user, vendedor=vendedor, tipo_entrega=tipo_entrega, direccion_data=direccion_data,
            )
        except (CarritoVacioError, StockInsuficienteError) as exc:
            return error_response(message=str(exc), status=400)

        return success_response(
            data=PedidoSerializer(pedido).data,
            message='Pedido creado correctamente. Estado: Pendiente de pago.',
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='subir-comprobante')
    def subir_comprobante(self, request, pk=None):
        pedido = self.get_object()
        if hasattr(pedido, 'comprobante_pago'):
            return error_response(message='Este pedido ya tiene un comprobante de pago registrado.', status=400)

        archivo = request.FILES.get('archivo')
        if archivo:
            validar_imagen(archivo)

        data = request.data.copy()
        data['pedido'] = pedido.pk
        if archivo:
            data['archivo'] = archivo

        serializer = ComprobantePagoSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        pedido.cambiar_estado(
            EstadoPedido.COMPROBANTE_ENVIADO,
            comentario='Comprobante subido por el cliente',
            usuario_responsable=request.user,
        )

        from tienda.services.email_service import notificar_comprobante_recibido
        notificar_comprobante_recibido(pedido)

        return success_response(
            data=serializer.data,
            message='Comprobante subido exitosamente. El pago está en proceso de revisión.',
            status=status.HTTP_201_CREATED,
        )


    @action(detail=True, methods=['patch'], url_path='definir-costo-envio', permission_classes=[EsAdministrador])
    def definir_costo_envio(self, request, pk=None):
        """El administrador define/edita manualmente el costo de envío según distancia/zona."""
        pedido = self.get_object()
        serializer = DefinirCostoEnvioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pedido.costo_envio = serializer.validated_data['costo_envio']
        pedido.costo_envio_definido = True
        pedido.save(update_fields=['costo_envio', 'costo_envio_definido'])
        pedido.recalcular_total()

        return success_response(data=PedidoSerializer(pedido).data, message='Costo de envío actualizado correctamente.')

    @action(detail=True, methods=['post'], url_path='marcar-contactado', permission_classes=[EsAdministradorOContador])
    def marcar_contactado(self, request, pk=None):
        pedido = self.get_object()
        pedido.cambiar_estado(
            EstadoPedido.PAGO_EN_REVISION,
            comentario='Equipo de soporte se puso en contacto con el cliente',
            usuario_responsable=request.user,
        )
        return success_response(data=PedidoSerializer(pedido).data, message='Estado actualizado: Pago en revisión.')

    @action(detail=True, methods=['post'], url_path='marcar-enviado', permission_classes=[EsAdministrador])
    def marcar_enviado(self, request, pk=None):
        pedido = self.get_object()
        pedido = marcar_pedido_enviado(pedido, usuario_responsable=request.user)
        return success_response(data=PedidoSerializer(pedido).data, message='Pedido marcado como enviado.')

    @action(detail=False, methods=['get'], url_path='comprobantes/pendientes', permission_classes=[EsAdministradorOContador])
    def comprobantes_pendientes(self, request):
        comprobantes = ComprobantePago.objects.filter(estado='PENDIENTE').select_related('pedido', 'pedido__usuario')
        return success_response(
            data=ComprobantePagoSerializer(comprobantes, many=True).data,
            message='Comprobantes pendientes obtenidos exitosamente.',
        )


class VerificarComprobanteView(viewsets.ViewSet):
    permission_classes = [EsAdministradorOContador]

    def partial_update(self, request, pk=None):
        comprobante = ComprobantePago.objects.filter(pk=pk).first()
        if not comprobante:
            return error_response(message='Comprobante no encontrado.', status=404)

        serializer = VerificarComprobanteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comprobante.estado = serializer.validated_data['estado']
        comprobante.observacion = serializer.validated_data.get('observacion', '')
        comprobante.verificado_por = request.user
        comprobante.save()  # dispara tienda/signals.py

        estado_msg = "aprobado" if comprobante.estado == 'VERIFICADO' else "rechazado"
        return success_response(
            data=ComprobantePagoSerializer(comprobante).data,
            message=f'Pago del comprobante #{pk} {estado_msg} correctamente.',
        )


class HistorialComprasView(APIView):
    """Historial completo de pedidos pasados del usuario autenticado."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        pedidos = Pedido.objects.filter(usuario=request.user).prefetch_related('detalles', 'historial')
        return success_response(
            data=PedidoSerializer(pedidos, many=True).data,
            message='Historial de compras obtenido exitosamente.',
        )
