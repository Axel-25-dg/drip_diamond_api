from rest_framework import serializers

from seguridad_acceso.models import IntentoLogin, IPBloqueada, LogAuditoria, SesionUsuario


class IntentoLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntentoLogin
        fields = ['id', 'username_intentado', 'ip', 'exitoso', 'fecha']


class IPBloqueadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPBloqueada
        fields = ['id', 'ip', 'motivo', 'bloqueada_en', 'desbloquear_en']


class LogAuditoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogAuditoria
        fields = ['id', 'usuario', 'accion', 'modelo_afectado', 'objeto_id', 'detalle', 'ip', 'fecha']


class SesionUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = SesionUsuario
        fields = ['id', 'usuario', 'ip', 'user_agent', 'iniciada_en', 'activa']
