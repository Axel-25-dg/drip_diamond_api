from rest_framework import mixins, permissions, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView

from core.responses import success_response
from tienda.models import ImagenAdjunta
from tienda.permissions import SoloLecturaOAdministrador
from tienda.serializers.imagen_serializers import ImagenAdjuntaSerializer, SubirImagenSerializer
from tienda.services.imagen_service import validar_imagen


class SubirImagenView(APIView):
    """
    Endpoint único y reutilizable para subir una imagen y asociarla a
    cualquier modelo (producto, marca, promoción, etc.) vía GenericForeignKey.
    Devuelve {id, url} como pide la especificación del sistema.

    POST multipart/form-data:
      archivo, app_label, model, object_id, es_principal (opcional), orden (opcional)
    """
    permission_classes = [permissions.IsAuthenticated, SoloLecturaOAdministrador]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = SubirImagenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        validar_imagen(datos['archivo'])

        imagen = ImagenAdjunta.objects.create(
            archivo=datos['archivo'],
            content_type=datos['content_type'],
            object_id=datos['object_id'],
            es_principal=datos.get('es_principal', False),
            orden=datos.get('orden', 0),
        )

        url_completa = request.build_absolute_uri(imagen.archivo.url)

        return success_response(
            data={'id': imagen.id, 'url': url_completa},
            message='Imagen subida exitosamente.',
            status=status.HTTP_201_CREATED,
        )


class ImagenAdjuntaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Listar/consultar imágenes de un objeto: ?content_type=<id>&object_id=<id>, o eliminarlas por id."""
    queryset = ImagenAdjunta.objects.all()
    serializer_class = ImagenAdjuntaSerializer
    permission_classes = [SoloLecturaOAdministrador]
    filterset_fields = ['content_type', 'object_id']

    def get_serializer_context(self):
        return {'request': self.request}
