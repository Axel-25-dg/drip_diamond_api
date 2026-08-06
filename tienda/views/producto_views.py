from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from tienda.filters import ProductoFilter
from tienda.models import Categoria, FotoProducto, Marca, Producto, Promocion, Talla, VarianteProducto
from tienda.permissions import SoloLecturaOAdministrador
from tienda.serializers.producto_serializers import (
    CategoriaSerializer,
    FotoProductoSerializer,
    MarcaSerializer,
    ProductoDetalleSerializer,
    ProductoListaSerializer,
    PromocionSerializer,
    TallaSerializer,
    VarianteProductoSerializer,
)


class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [SoloLecturaOAdministrador]
    parser_classes = [MultiPartParser, FormParser]


class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [SoloLecturaOAdministrador]


class TallaViewSet(viewsets.ModelViewSet):
    queryset = Talla.objects.all()
    serializer_class = TallaSerializer
    permission_classes = [SoloLecturaOAdministrador]


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.filter(activo=True).select_related('marca', 'categoria').prefetch_related(
        'fotos', 'variantes', 'promociones'
    )
    permission_classes = [SoloLecturaOAdministrador]
    filterset_class = ProductoFilter
    search_fields = ['nombre', 'modelo', 'marca__nombre']
    ordering_fields = ['precio_base', 'creado_en']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductoListaSerializer
        return ProductoDetalleSerializer


class VarianteProductoViewSet(viewsets.ModelViewSet):
    queryset = VarianteProducto.objects.select_related('producto', 'talla')
    serializer_class = VarianteProductoSerializer
    permission_classes = [SoloLecturaOAdministrador]
    filterset_fields = ['producto', 'talla']


class FotoProductoViewSet(viewsets.ModelViewSet):
    """El archivo se sube directo (multipart) y queda alojado en Cloudinary, nunca por URL manual."""
    queryset = FotoProducto.objects.all()
    serializer_class = FotoProductoSerializer
    permission_classes = [SoloLecturaOAdministrador]
    parser_classes = [MultiPartParser, FormParser]
    filterset_fields = ['producto']


class PromocionViewSet(viewsets.ModelViewSet):
    queryset = Promocion.objects.select_related('producto')
    serializer_class = PromocionSerializer
    permission_classes = [SoloLecturaOAdministrador]
    filterset_fields = ['producto', 'activo']

    @action(detail=True, methods=['post'], url_path='notificar-clientes')
    def notificar_clientes(self, request, pk=None):
        """El administrador dispara el aviso de la promoción a todos los clientes."""
        from tienda.models import Rol, Usuario
        from tienda.services.email_service import notificar_promocion

        promocion = self.get_object()
        clientes = Usuario.objects.filter(rol=Rol.CLIENTE)
        for cliente in clientes:
            notificar_promocion(cliente, promocion.producto, promocion)
        return Response({'detail': f'Promoción notificada a {clientes.count()} clientes.'})
