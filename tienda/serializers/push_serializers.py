from rest_framework import serializers
from tienda.models import SuscripcionPush, CampanaNotificacionPush, SegmentoPush, Usuario


class SuscripcionPushSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuscripcionPush
        fields = ['id', 'endpoint', 'p256dh', 'auth', 'user_agent', 'activa', 'creada_en']
        read_only_fields = ['id', 'activa', 'creada_en']


class RegistrarSuscripcionPushSerializer(serializers.Serializer):
    endpoint = serializers.URLField(max_length=700)
    keys = serializers.DictField(child=serializers.CharField())
    user_agent = serializers.CharField(max_length=300, required=False, allow_blank=True)

    def validate_keys(self, value):
        if 'p256dh' not in value or 'auth' not in value:
            raise serializers.ValidationError("Las claves 'p256dh' y 'auth' son obligatorias.")
        return value


class DesuscribirPushSerializer(serializers.Serializer):
    endpoint = serializers.URLField(max_length=700)


class EnviarPushCustomAdminSerializer(serializers.Serializer):
    titulo = serializers.CharField(max_length=120)
    cuerpo = serializers.CharField(max_length=500)
    icono_url = serializers.URLField(max_length=500, required=False, allow_blank=True, default='')
    imagen_url = serializers.URLField(max_length=500, required=False, allow_blank=True, default='')
    url_destino = serializers.CharField(max_length=300, required=False, default='/')
    badge_url = serializers.URLField(max_length=500, required=False, allow_blank=True, default='')
    sonido_activo = serializers.BooleanField(default=True)
    vibracion_activa = serializers.BooleanField(default=True)
    segmento = serializers.ChoiceField(choices=SegmentoPush.choices, default=SegmentoPush.TODOS)
    usuarios_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=[])


class CampanaNotificacionPushSerializer(serializers.ModelSerializer):
    creado_por_nombre = serializers.ReadOnlyField(source='creado_por.nombre_completo')

    class Meta:
        model = CampanaNotificacionPush
        fields = [
            'id', 'titulo', 'cuerpo', 'icono_url', 'imagen_url', 'url_destino',
            'badge_url', 'sonido_activo', 'vibracion_activa', 'segmento',
            'total_enviados', 'total_exitosos', 'total_fallidos', 'creada_en',
            'creado_por_nombre'
        ]
