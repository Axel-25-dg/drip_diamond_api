from rest_framework import viewsets

from tienda.models import CostoEnvioZona
from tienda.permissions import SoloLecturaOAdministrador
from tienda.serializers.envio_serializers import CostoEnvioZonaSerializer


class CostoEnvioZonaViewSet(viewsets.ModelViewSet):
    queryset = CostoEnvioZona.objects.all()
    serializer_class = CostoEnvioZonaSerializer
    permission_classes = [SoloLecturaOAdministrador]
    filterset_fields = ['ciudad', 'activo']
