from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from tienda.models import ImagenAdjunta


class ImagenAdjuntaSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ImagenAdjunta
        fields = ['id', 'url', 'orden', 'es_principal', 'creada_en']

    def get_url(self, obj):
        request = self.context.get('request')
        url = obj.archivo.url
        return request.build_absolute_uri(url) if request else url


class SubirImagenSerializer(serializers.Serializer):
    """
    Input genérico para asociar una imagen a CUALQUIER modelo del sistema:
    archivo (multipart), app_label + model (ej: 'tienda', 'producto'), object_id.
    """
    archivo = serializers.ImageField()
    app_label = serializers.CharField(max_length=100)
    model = serializers.CharField(max_length=100)
    object_id = serializers.IntegerField()
    es_principal = serializers.BooleanField(required=False, default=False)
    orden = serializers.IntegerField(required=False, default=0)

    def validate(self, datos):
        try:
            content_type = ContentType.objects.get(app_label=datos['app_label'], model=datos['model'].lower())
        except ContentType.DoesNotExist:
            raise serializers.ValidationError('No existe ese modelo (app_label/model no reconocidos).')

        modelo_clase = content_type.model_class()
        if not modelo_clase.objects.filter(pk=datos['object_id']).exists():
            raise serializers.ValidationError('No existe un objeto con ese ID para ese modelo.')

        datos['content_type'] = content_type
        return datos
