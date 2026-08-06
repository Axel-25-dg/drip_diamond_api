from rest_framework import serializers

from tienda.models import CostoEnvioZona


class CostoEnvioZonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostoEnvioZona
        fields = ['id', 'ciudad', 'costo_domicilio', 'costo_retiro_local', 'activo']
