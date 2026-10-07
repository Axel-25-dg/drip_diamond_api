from rest_framework import mixins, permissions, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView

from core.responses import success_response, error_response
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

        try:
            validar_imagen(datos['archivo'])
        except Exception as e:
            return error_response(
                message=f"Imagen no válida: {str(e)}",
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            instancia = datos['model_class'].objects.get(pk=datos['object_id'])
            field_name = datos['field_name']

            setattr(instancia, field_name, datos['archivo'])
            instancia.save(update_fields=[field_name])

            campo_archivo = getattr(instancia, field_name)
            url_archivo = campo_archivo.url
            if not url_archivo.startswith('http'):
                url_archivo = request.build_absolute_uri(url_archivo)

            data_res = {'id': instancia.pk, 'url': url_archivo, 'field': field_name}
            try:
                from tienda.models.archivo_db import ArchivoAlmacenado
                import base64
                archivo_db = ArchivoAlmacenado.objects.filter(nombre=campo_archivo.name).first()
                if archivo_db:
                    b64 = base64.b64encode(bytes(archivo_db.datos)).decode('ascii')
                    data_res['data_uri'] = f"data:{archivo_db.content_type};base64,{b64}"
            except Exception:
                pass

            return success_response(
                data=data_res,
                message='Imagen subida exitosamente.',
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return error_response(
                message=f"Error al guardar la imagen: {str(e)}",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
