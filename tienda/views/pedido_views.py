from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from tienda.models import ComprobantePago, Pedido, Rol, Usuario
from tienda.permissions import EsAdministrador, EsAdministradorOContador, EsDuenoOAdministrador
from tienda.serializers.pedido_serializers import (
    ComprobantePagoSerializer,
    CrearPedidoSerializer,
    DefinirCostoEnvioSerializer,
    PedidoSerializer,
    VerificarComprobanteSerializer,
)
from tienda.services.envio_service import marcar_pedido_enviado
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

    def create(self, request, *args, **kwargs):
        serializer = CrearPedidoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        vendedor = Usuario.objects.filter(pk=datos.pop('vendedor_id'), rol=Rol.VENDEDOR).first()
        if not vendedor:
            return Response({'detail': 'Vendedor no válido.'}, status=status.HTTP_400_BAD_REQUEST)

        tipo_entrega = datos.pop('tipo_entrega')
        direccion_data = datos  # el resto ya son los campos de DireccionEnvioPedido

        try:
            pedido = crear_pedido_desde_carrito(
                usuario=request.user, vendedor=vendedor, tipo_entrega=tipo_entrega, direccion_data=direccion_data,
            )
        except (CarritoVacioError, StockInsuficienteError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PedidoSerializer(pedido).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='subir-comprobante')
    def subir_comprobante(self, request, pk=None):
        pedido = self.get_object()
        if hasattr(pedido, 'comprobante_pago'):
            return Response({'detail': 'Este pedido ya tiene un comprobante.'}, status=400)

        serializer = ComprobantePagoSerializer(data={**request.data, 'pedido': pedido.pk})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        pedido.cambiar_estado('PAGO_SUBIDO', comentario='Comprobante subido por el cliente', usuario_responsable=request.user)

        from tienda.services.email_service import notificar_comprobante_recibido
        notificar_comprobante_recibido(pedido)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], url_path='definir-costo-envio', permission_classes=[EsAdministrador])
    def definir_costo_envio(self, request, pk=None):
        """El administrador define/edita manualmente el costo de envío según distancia/ciudad."""
        pedido = self.get_object()
        serializer = DefinirCostoEnvioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pedido.costo_envio = serializer.validated_data['costo_envio']
        pedido.costo_envio_definido = True
        pedido.save(update_fields=['costo_envio', 'costo_envio_definido'])
        pedido.recalcular_total()

        return Response(PedidoSerializer(pedido).data)

    @action(detail=True, methods=['post'], url_path='marcar-contactado', permission_classes=[EsAdministradorOContador])
    def marcar_contactado(self, request, pk=None):
        pedido = self.get_object()
        pedido.cambiar_estado('CONTACTADO', comentario='Equipo se puso en contacto con el cliente', usuario_responsable=request.user)
        return Response(PedidoSerializer(pedido).data)

    @action(detail=True, methods=['post'], url_path='marcar-enviado', permission_classes=[EsAdministrador])
    def marcar_enviado(self, request, pk=None):
        pedido = self.get_object()
        pedido = marcar_pedido_enviado(pedido, usuario_responsable=request.user)
        return Response(PedidoSerializer(pedido).data)


class VerificarComprobanteView(viewsets.ViewSet):
    permission_classes = [EsAdministradorOContador]

    def partial_update(self, request, pk=None):
        comprobante = ComprobantePago.objects.filter(pk=pk).first()
        if not comprobante:
            return Response({'detail': 'Comprobante no encontrado.'}, status=404)

        serializer = VerificarComprobanteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comprobante.estado = serializer.validated_data['estado']
        comprobante.observacion = serializer.validated_data.get('observacion', '')
        comprobante.verificado_por = request.user
        comprobante.save()  # dispara tienda/signals.py

        return Response(ComprobantePagoSerializer(comprobante).data)


class HistorialComprasView(APIView):
    """Historial completo de pedidos pasados del usuario autenticado."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        pedidos = Pedido.objects.filter(usuario=request.user).prefetch_related('detalles', 'historial')
        return Response(PedidoSerializer(pedidos, many=True).data)
