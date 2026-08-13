from rest_framework import serializers

from tienda.models import ComisionVenta, LiquidacionMensual


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


class ResumenVendedorSerializer(serializers.Serializer):
    """Resumen consolidado de un vendedor para la vista de liquidaciones del contador."""
    vendedor_id = serializers.IntegerField()
    vendedor_nombre = serializers.CharField()
    vendedor_email = serializers.EmailField()
    total_pares_mes = serializers.IntegerField()
    total_comisiones_mes = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_comisiones_historico = serializers.DecimalField(max_digits=10, decimal_places=2)
    liquidacion_id = serializers.IntegerField(allow_null=True)
    liquidacion_pagada = serializers.BooleanField()
    fecha_pago = serializers.DateTimeField(allow_null=True)
    comprobante_pago_url = serializers.CharField(allow_null=True)
