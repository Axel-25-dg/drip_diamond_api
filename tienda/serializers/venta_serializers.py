from rest_framework import serializers

from tienda.models import ComisionVenta, LiquidacionMensual, MensajeChatPedido


class ComisionVentaSerializer(serializers.ModelSerializer):
    pedido_id = serializers.IntegerField(source='pedido.id', read_only=True)

    class Meta:
        model = ComisionVenta
        fields = [
            'id', 'pedido_id', 'vendedor', 'cantidad_pares', 'monto_por_par',
            'monto', 'estado', 'confirmada_por', 'generada_en',
        ]


class LiquidacionMensualSerializer(serializers.ModelSerializer):
    comisiones = ComisionVentaSerializer(many=True, read_only=True)

    class Meta:
        model = LiquidacionMensual
        fields = [
            'id', 'vendedor', 'periodo_anio', 'periodo_mes', 'total_pares', 'total_comisiones',
            'pagada', 'marcada_pagada_por', 'fecha_pago', 'comprobante_pago', 'comisiones', 'creada_en',
        ]
        read_only_fields = ['total_pares', 'total_comisiones', 'pagada', 'marcada_pagada_por', 'fecha_pago']


class GenerarLiquidacionSerializer(serializers.Serializer):
    vendedor_id = serializers.IntegerField()
    anio = serializers.IntegerField()
    mes = serializers.IntegerField(min_value=1, max_value=12)


class MarcarPagadaSerializer(serializers.Serializer):
    comprobante_pago = serializers.FileField()


class MensajeChatPedidoSerializer(serializers.ModelSerializer):
    remitente_nombre = serializers.CharField(source='remitente.nombre_completo', read_only=True)

    class Meta:
        model = MensajeChatPedido
        fields = ['id', 'pedido', 'remitente', 'remitente_nombre', 'mensaje', 'es_confirmacion_entrega', 'enviado_en']
        read_only_fields = ['remitente', 'es_confirmacion_entrega']
