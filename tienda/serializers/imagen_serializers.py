from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers


class SubirImagenSerializer(serializers.Serializer):
    """
    Input genérico para asociar una imagen a un modelo del sistema usando ImageField nativos.
    """
    archivo = serializers.ImageField()
    app_label = serializers.CharField(max_length=100)
    model = serializers.CharField(max_length=100)
    object_id = serializers.IntegerField()

    def validate(self, datos):
        try:
            content_type = ContentType.objects.get(app_label=datos['app_label'], model=datos['model'].lower())
        except ContentType.DoesNotExist:
            raise serializers.ValidationError('No existe ese modelo (app_label/model no reconocidos).')

        modelo_clase = content_type.model_class()
        if not modelo_clase or not modelo_clase.objects.filter(pk=datos['object_id']).exists():
            raise serializers.ValidationError('No existe un objeto con ese ID para ese modelo.')

        field_name = self._obtener_campo_imagen(modelo_clase)
        if not field_name:
            raise serializers.ValidationError('Ese modelo no tiene un campo de imagen compatible.')

        datos['content_type'] = content_type
        datos['model_class'] = modelo_clase
        datos['field_name'] = field_name
        return datos

    def _obtener_campo_imagen(self, modelo_clase):
        for campo in ('imagen', 'imagen_principal', 'logo', 'foto_perfil'):
            if campo in [field.name for field in modelo_clase._meta.get_fields()]:
                return campo
        return None
