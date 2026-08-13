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
    producto_nombre = serializers.SerializerMethodField()
    marca = serializers.SerializerMethodField()
    talla = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = ItemCarrito
        fields = ['id', 'variante_producto', 'variante_producto_id', 'cantidad', 'subtotal',
                  'producto_nombre', 'marca', 'talla', 'color', 'imagen_url']

    def get_producto_nombre(self, obj):
        try: return obj.variante_producto.producto.nombre
        except Exception: return ''

    def get_marca(self, obj):
        try: return obj.variante_producto.producto.marca.nombre
        except Exception: return ''

    def get_talla(self, obj):
        try: return obj.variante_producto.talla.valor
        except Exception: return ''

    def get_color(self, obj):
        try: return obj.variante_producto.color or 'Estandar'
        except Exception: return ''

    def get_imagen_url(self, obj):
        try:
            img = obj.variante_producto.producto.imagen_principal
            if not img: return None
            request = self.context.get('request')
            return request.build_absolute_uri(img.url) if request else img.url
        except Exception: return None

class CarritoSerializer(serializers.ModelSerializer):
    items = ItemCarritoSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Carrito
        fields = ['id', 'items', 'subtotal', 'actualizado_en']


class DetallePedidoSerializer(serializers.ModelSerializer):
    variante_producto = VarianteProductoSerializer(read_only=True)
    producto_nombre = serializers.SerializerMethodField()
    talla = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = DetallePedido
        fields = ['id', 'variante_producto', 'cantidad', 'precio_unitario', 'subtotal',
                  'producto_nombre', 'talla', 'color', 'imagen_url']

    def get_producto_nombre(self, obj):
        try: return obj.variante_producto.producto.nombre
        except Exception: return ''

    def get_talla(self, obj):
        try: return str(obj.variante_producto.talla.valor)
        except Exception: return ''

    def get_color(self, obj):
        try: return obj.variante_producto.color or 'Estandar'
        except Exception: return ''

    def get_imagen_url(self, obj):
        try:
            img = obj.variante_producto.producto.imagen_principal
            if not img: return None
            request = self.context.get('request')
            return request.build_absolute_uri(img.url) if request else img.url
        except Exception: return None


class DireccionEnvioPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DireccionEnvioPedido
        fields = [
            'direccion_formateada', 'referencia_adicional', 'ciudad', 'provincia', 'telefono_contacto',
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
    vendedor_codigo = serializers.CharField(source='vendedor.perfil_vendedor.codigo_vendedor', read_only=True, default=None)

    # Campos calculados para el frontend
    cliente_nombre = serializers.SerializerMethodField()
    cliente_telefono = serializers.SerializerMethodField()
    cliente_email = serializers.SerializerMethodField()
    vendedor_nombre = serializers.SerializerMethodField()
    provincia = serializers.SerializerMethodField()
    numero = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = [
            'id', 'numero', 'usuario', 'cliente_nombre', 'cliente_telefono', 'cliente_email',
            'vendedor', 'vendedor_nombre', 'vendedor_codigo', 'tipo_entrega',
            'direccion_envio', 'provincia', 'costo_envio', 'costo_envio_definido',
            'subtotal', 'total', 'estado', 'numero_guia',
            'detalles', 'historial', 'comprobante_pago',
            'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['usuario', 'subtotal', 'total', 'estado', 'numero_guia']

    def get_numero(self, obj):
        return f'#{obj.pk}'

    def get_cliente_nombre(self, obj):
        u = obj.usuario
        if not u:
            return None
        partes = [
            u.primer_nombre or getattr(u, 'first_name', '') or '',
            u.primer_apellido or getattr(u, 'last_name', '') or '',
        ]
        nombre = ' '.join(p for p in partes if p).strip()
        return nombre or u.username or None

    def get_cliente_telefono(self, obj):
        # Prefer the phone from the shipping address (entered at checkout)
        try:
            t = obj.direccion_envio.telefono_contacto
            if t:
                return t
        except Exception:
            pass
        u = obj.usuario
        if not u:
            return ''
        return getattr(u, 'telefono', '') or ''

    def get_cliente_email(self, obj):
        u = obj.usuario
        if not u:
            return ''
        return getattr(u, 'email', '') or ''

    def get_vendedor_nombre(self, obj):
        v = obj.vendedor
        if not v:
            return None
        partes = [
            v.primer_nombre or getattr(v, 'first_name', '') or '',
            v.primer_apellido or getattr(v, 'last_name', '') or '',
        ]
        nombre = ' '.join(p for p in partes if p).strip()
        return nombre or v.username or None

    def get_provincia(self, obj):
        try:
            return obj.direccion_envio.provincia or ''
        except Exception:
            return ''


class CrearPedidoSerializer(serializers.Serializer):
    """Input para generar el pedido a partir del carrito."""
    vendedor_id = serializers.IntegerField(required=False, allow_null=True)
    tipo_entrega = serializers.ChoiceField(choices=['DOMICILIO', 'RETIRO_LOCAL'], required=False, default='DOMICILIO')

    direccion_formateada = serializers.CharField(max_length=255, required=False, allow_blank=True)
    direccion_envio = serializers.CharField(max_length=255, required=False, allow_blank=True)
    referencia_adicional = serializers.CharField(max_length=255, required=False, allow_blank=True)
    ciudad = serializers.CharField(max_length=100, required=False, allow_blank=True)
    provincia = serializers.CharField(max_length=100, required=False, allow_blank=True)
    telefono_contacto = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate(self, attrs):
        if 'direccion_envio' in attrs and not attrs.get('direccion_formateada'):
            attrs['direccion_formateada'] = attrs.pop('direccion_envio')
        elif 'direccion_envio' in attrs:
            attrs.pop('direccion_envio')

        if not attrs.get('direccion_formateada'):
            attrs['direccion_formateada'] = 'Retiro en local' if attrs.get('tipo_entrega') == 'RETIRO_LOCAL' else 'Direccion no especificada'

        if not attrs.get('ciudad'):
            attrs['ciudad'] = 'Quito'

        return attrs


class DefinirCostoEnvioSerializer(serializers.Serializer):
    costo_envio = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0)




