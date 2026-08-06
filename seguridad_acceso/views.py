from rest_framework import viewsets

from seguridad_acceso.models import IntentoLogin, IPBloqueada, LogAuditoria
from seguridad_acceso.serializers import IntentoLoginSerializer, IPBloqueadaSerializer, LogAuditoriaSerializer
from tienda.permissions import EsAdministrador


class IntentoLoginViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IntentoLogin.objects.all()
    serializer_class = IntentoLoginSerializer
    permission_classes = [EsAdministrador]
    filterset_fields = ['exitoso', 'ip']


class IPBloqueadaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IPBloqueada.objects.all()
    serializer_class = IPBloqueadaSerializer
    permission_classes = [EsAdministrador]


class LogAuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LogAuditoria.objects.select_related('usuario').all()
    serializer_class = LogAuditoriaSerializer
    permission_classes = [EsAdministrador]
    filterset_fields = ['modelo_afectado', 'usuario']
