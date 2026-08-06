from rest_framework import serializers

from tienda.models import CampanaEmail, EstadoCampana, SegmentoCampana


class CampanaEmailSerializer(serializers.ModelSerializer):
    creada_por_nombre = serializers.CharField(
        source='creada_por.nombre_completo', read_only=True, default=None
    )
    segmento_display = serializers.CharField(source='get_segmento_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = CampanaEmail
        fields = [
            'id',
            'titulo',
            'asunto',
            'contenido_html',
            'segmento',
            'segmento_display',
            'estado',
            'estado_display',
            'programado_para',
            'total_destinatarios',
            'total_enviados',
            'total_fallidos',
            'creada_por',
            'creada_por_nombre',
            'creada_en',
            'enviada_en',
        ]
        read_only_fields = [
            'id', 'estado', 'total_destinatarios', 'total_enviados',
            'total_fallidos', 'creada_por', 'creada_en', 'enviada_en',
            'segmento_display', 'estado_display', 'creada_por_nombre',
        ]


class CampanaEmailListSerializer(serializers.ModelSerializer):
    """Serializer compacto para listados."""
    segmento_display = serializers.CharField(source='get_segmento_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = CampanaEmail
        fields = [
            'id', 'titulo', 'asunto', 'segmento', 'segmento_display',
            'estado', 'estado_display', 'total_destinatarios',
            'total_enviados', 'total_fallidos', 'creada_en', 'enviada_en',
        ]
