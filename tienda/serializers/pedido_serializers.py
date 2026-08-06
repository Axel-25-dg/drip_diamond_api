from rest_framework import serializers

from tienda.models import (
    Carrito,
    ComprobantePago,
    DetallePedido,
    DireccionEnvioPedido,
    HistorialEstadoPedido,
    ItemCarrito,
    Pedido,
    VarianteProducto,
)
from tienda.serializers.producto_serializers import VarianteProductoSerializer


class ItemCarritoSerializer(serializers.ModelSerializer):
    variante_producto = VarianteProductoSerializer(read_only=True)
    variante_producto_id = serializers.PrimaryKeyRelatedField(
        queryset=VarianteProducto.objects.all(), source='variante_producto', write_only=True
    )
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = ItemCarrito
        fields = ['id', 'variante_producto', 'variante_producto_id', 'cantidad', 'subtotal']


class CarritoSerializer(serializers.ModelSerializer):
    items = ItemCarritoSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Carrito
        fields = ['id', 'items', 'subtotal', 'actualizado_en']


class DetallePedidoSerializer(serializers.ModelSerializer):
    variante_producto = VarianteProductoSerializer(read_only=True)

    class Meta:
        model = DetallePedido
        fields = ['id', 'variante_producto', 'cantidad', 'precio_unitario', 'subtotal']


class DireccionEnvioPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DireccionEnvioPedido
        fields = [
            'direccion_formateada', 'referencia_adicional', 'ciudad',
        ]


class HistorialEstadoPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialEstadoPedido
        fields = ['estado', 'comentario', 'fecha']


class ComprobantePagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComprobantePago
        fields = [
            'id', 'pedido', 'archivo', 'banco_origen', 'numero_referencia',
            'monto_declarado', 'estado', 'verificado_por', 'fecha_verificacion',
            'observacion', 'subido_en',
        ]
        read_only_fields = ['estado', 'verificado_por', 'fecha_verificacion']


class VerificarComprobanteSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=['VERIFICADO', 'RECHAZADO'])
    observacion = serializers.CharField(required=False, allow_blank=True)


class PedidoSerializer(serializers.ModelSerializer):
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    historial = HistorialEstadoPedidoSerializer(many=True, read_only=True)
    comprobante_pago = ComprobantePagoSerializer(read_only=True)
    direccion_envio = DireccionEnvioPedidoSerializer(read_only=True)
    vendedor_codigo = serializers.CharField(source='vendedor.perfil_vendedor.codigo_vendedor', read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id', 'usuario', 'vendedor', 'vendedor_codigo', 'tipo_entrega',
            'direccion_envio', 'costo_envio', 'costo_envio_definido',
            'subtotal', 'total', 'estado', 'numero_guia',
            'detalles', 'historial', 'comprobante_pago',
            'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['usuario', 'subtotal', 'total', 'estado', 'numero_guia']


class CrearPedidoSerializer(serializers.Serializer):
    """Input para generar el pedido a partir del carrito + dirección exacta de envío."""
    vendedor_id = serializers.IntegerField()
    tipo_entrega = serializers.ChoiceField(choices=['DOMICILIO', 'RETIRO_LOCAL'])

    direccion_formateada = serializers.CharField(max_length=255)
    referencia_adicional = serializers.CharField(max_length=255, required=False, allow_blank=True)
    ciudad = serializers.CharField(max_length=100)


class DefinirCostoEnvioSerializer(serializers.Serializer):
    """Solo el administrador: define/edita manualmente el costo de envío de un pedido puntual."""
    costo_envio = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0)
