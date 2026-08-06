from rest_framework import serializers

from tienda.models import Categoria, Marca, Producto, Promocion, Talla, VarianteProducto
from tienda.serializers.imagen_serializers import ImagenAdjuntaSerializer


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ['id', 'nombre', 'logo', 'activa']


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion']


class TallaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Talla
        fields = ['id', 'valor']


class PromocionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promocion
        fields = ['id', 'producto', 'precio_promocional', 'fecha_inicio', 'fecha_fin', 'activo']


class VarianteProductoSerializer(serializers.ModelSerializer):
    talla = TallaSerializer(read_only=True)
    talla_id = serializers.PrimaryKeyRelatedField(queryset=Talla.objects.all(), source='talla', write_only=True)
    disponible = serializers.BooleanField(read_only=True)

    class Meta:
        model = VarianteProducto
        fields = ['id', 'talla', 'talla_id', 'stock', 'peso_kg', 'sku', 'disponible']


class ProductoListaSerializer(serializers.ModelSerializer):
    marca = serializers.CharField(source='marca.nombre', read_only=True)
    foto_principal = serializers.SerializerMethodField()
    tallas_disponibles = serializers.SerializerMethodField()
    precio_actual = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    en_promocion = serializers.SerializerMethodField()
    disponible = serializers.BooleanField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'marca', 'calidad', 'precio_base', 'precio_actual',
            'en_promocion', 'disponible', 'foto_principal', 'tallas_disponibles',
        ]

    def get_foto_principal(self, obj):
        imagen = obj.imagenes.filter(es_principal=True).first() or obj.imagenes.first()
        if not imagen:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(imagen.archivo.url) if request else imagen.archivo.url

    def get_tallas_disponibles(self, obj):
        return [v.talla.valor for v in obj.variantes.filter(stock__gt=0)]

    def get_en_promocion(self, obj):
        return obj.promocion_vigente is not None


class ProductoDetalleSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer(read_only=True)
    marca_id = serializers.PrimaryKeyRelatedField(queryset=Marca.objects.all(), source='marca', write_only=True)
    categoria = CategoriaSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), source='categoria', write_only=True, required=False
    )
    imagenes = ImagenAdjuntaSerializer(many=True, read_only=True)
    variantes = VarianteProductoSerializer(many=True, read_only=True)
    promociones = PromocionSerializer(many=True, read_only=True)
    precio_actual = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    disponible = serializers.BooleanField(read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id', 'marca', 'marca_id', 'categoria', 'categoria_id',
            'nombre', 'modelo', 'calidad', 'descripcion', 'precio_base', 'precio_actual',
            'activo', 'disponible', 'imagenes', 'variantes', 'promociones', 'creado_en',
        ]
        read_only_fields = ['id', 'creado_en']
