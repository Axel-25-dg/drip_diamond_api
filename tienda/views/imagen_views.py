from django.contrib.contenttypes.models import ContentType
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView

from core.responses import success_response
from tienda.permissions import SoloLecturaOAdministrador
from tienda.serializers.imagen_serializers import SubirImagenSerializer
from tienda.services.imagen_service import validar_imagen


class SubirImagenView(APIView):
    """
    Endpoint para subir imágenes y asociarlas directamente a un campo ImageField del modelo.
    Soporta campos como imagen, imagen_principal, logo y foto_perfil.
    """
    permission_classes = [permissions.IsAuthenticated, SoloLecturaOAdministrador]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = SubirImagenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        validar_imagen(datos['archivo'])

        instancia = datos['model_class'].objects.get(pk=datos['object_id'])
        field_name = datos['field_name']
        setattr(instancia, field_name, datos['archivo'])
        instancia.save(update_fields=[field_name])

        url_completa = request.build_absolute_uri(getattr(instancia, field_name).url)

        return success_response(
            data={'id': instancia.pk, 'url': url_completa, 'field': field_name},
            message='Imagen subida exitosamente.',
            status=status.HTTP_201_CREATED,
        )


class ImagenAdjuntaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Compatibilidad temporal: devuelve una lista vacía y permite un flujo simple para el front."""
    permission_classes = [SoloLecturaOAdministrador]

    def list(self, request, *args, **kwargs):
        return success_response(data=[], message='El flujo de imágenes ahora usa los campos ImageField nativos del modelo.')

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=None, message='Esta ruta ya no se usa.', status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, *args, **kwargs):
        return success_response(data=None, message='La eliminación se realiza desde el modelo correspondiente.', status=status.HTTP_404_NOT_FOUND)
