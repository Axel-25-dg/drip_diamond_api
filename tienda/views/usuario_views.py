from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from tienda.models import Rol, Usuario
from tienda.permissions import EsAdministrador
from tienda.serializers.usuario_serializers import (
    CrearContadorSerializer,
    CrearVendedorSerializer,
    RegistroClienteSerializer,
    UsuarioSerializer,
)


class RegistroClienteView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = RegistroClienteSerializer
    permission_classes = [permissions.AllowAny]


class VerificarUsernameView(generics.GenericAPIView):
    """Para validar en vivo, en el formulario de registro/edición, que el username elegido esté libre."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from tienda.services.username_service import username_disponible

        username = request.query_params.get('username', '')
        return Response({'disponible': username_disponible(username)})


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.select_related('perfil_vendedor', 'perfil_contador')
    serializer_class = UsuarioSerializer
    permission_classes = [EsAdministrador]
    filterset_fields = ['rol']
    search_fields = ['username', 'email', 'primer_nombre', 'primer_apellido', 'cedula']

    @action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        if request.method == 'GET':
            return Response(UsuarioSerializer(request.user).data)
        serializer = UsuarioSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CrearVendedorView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = CrearVendedorSerializer
    permission_classes = [EsAdministrador]


class CrearContadorView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = CrearContadorSerializer
    permission_classes = [EsAdministrador]


class ListaVendedoresActivosView(generics.ListAPIView):
    """Lista pública (para usuarios autenticados) de vendedores activos, elección obligatoria en el checkout."""
    queryset = Usuario.objects.filter(rol=Rol.VENDEDOR, perfil_vendedor__activo=True)
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]
