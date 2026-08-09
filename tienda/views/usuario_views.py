from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from core.responses import success_response
from tienda.models import Rol, Usuario
from tienda.permissions import EsAdministrador
from tienda.serializers.usuario_serializers import (
    CrearContadorSerializer,
    CrearVendedorSerializer,
    RegistroClienteSerializer,
    UsuarioSerializer,
)
from tienda.services.email_service import notificar_bienvenida


class RegistroClienteView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = RegistroClienteSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        notificar_bienvenida(usuario)
        return success_response(
            data=UsuarioSerializer(usuario).data,
            message='Usuario registrado exitosamente. Se ha enviado un correo de bienvenida.',
            status=status.HTTP_201_CREATED,
        )



class VerificarUsernameView(generics.GenericAPIView):
    """Para validar en vivo, en el formulario de registro/ediciÃ³n, que el username elegido estÃ© libre."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from tienda.services.username_service import username_disponible

        username = request.query_params.get('username', '')
        disponible = username_disponible(username)
        return success_response(
            data={'disponible': disponible, 'username': username},
            message='VerificaciÃ³n de username realizada.',
        )


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.select_related('perfil_vendedor', 'perfil_contador')
    serializer_class = UsuarioSerializer
    permission_classes = [EsAdministrador]
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ['rol']
    search_fields = ['username', 'email', 'primer_nombre', 'primer_apellido']

    @action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAuthenticated],
             parser_classes=[MultiPartParser, FormParser, JSONParser])
    def me(self, request):
        if request.method == 'GET':
            return success_response(data=UsuarioSerializer(request.user, context={'request': request}).data)
        serializer = UsuarioSerializer(request.user, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success_response(data=serializer.data, message='Perfil actualizado exitosamente.')


class CrearVendedorView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = CrearVendedorSerializer
    permission_classes = [EsAdministrador]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendedor = serializer.save()
        return success_response(
            data=UsuarioSerializer(vendedor).data,
            message='Vendedor creado correctamente.',
            status=201,
        )


class CrearContadorView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = CrearContadorSerializer
    permission_classes = [EsAdministrador]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contador = serializer.save()
        return success_response(
            data=UsuarioSerializer(contador).data,
            message='Contador creado correctamente.',
            status=201,
        )


class ListaVendedoresActivosView(generics.ListAPIView):
    """Lista pÃºblica (para usuarios autenticados) de vendedores activos, elecciÃ³n obligatoria en el checkout."""
    queryset = Usuario.objects.filter(rol=Rol.VENDEDOR, perfil_vendedor__activo=True)
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data, message='Lista de vendedores activos retrieved.')
