from rest_framework import serializers

from tienda.models import Factura, LibroVentas, NotaCredito, Notificacion, ReporteSRI, RetencionImpuesto


class FacturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Factura
        fields = [
            'id', 'pedido', 'numero_secuencial', 'subtotal', 'iva_porcentaje',
            'iva_valor', 'total', 'estado', 'clave_acceso_sri', 'generada_en',
        ]
        read_only_fields = fields


class NotaCreditoSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaCredito
        fields = ['id', 'factura', 'motivo', 'valor', 'generada_en']


class RetencionImpuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetencionImpuesto
        fields = ['id', 'factura', 'porcentaje', 'valor_retenido', 'codigo_sri']


class LibroVentasSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibroVentas
        fields = ['id', 'anio', 'mes', 'total_ventas', 'total_iva', 'cerrado', 'generado_en']


class ReporteSRISerializer(serializers.ModelSerializer):
    libro_ventas = LibroVentasSerializer(read_only=True)

    class Meta:
        model = ReporteSRI
        fields = ['id', 'libro_ventas', 'archivo', 'generado_en']


class CerrarLibroVentasSerializer(serializers.Serializer):
    anio = serializers.IntegerField()
    mes = serializers.IntegerField(min_value=1, max_value=12)


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ['id', 'tipo', 'asunto', 'mensaje_corto', 'correo_enviado', 'leida', 'creada_en']
        read_only_fields = ['tipo', 'asunto', 'mensaje_corto', 'correo_enviado', 'creada_en']
