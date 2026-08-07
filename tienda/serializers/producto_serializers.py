from rest_framework import serializers

from tienda.models import Categoria, Marca, Producto, Promocion, Talla, VarianteProducto


class VarianteProductoCreateSerializer(serializers.ModelSerializer):
    talla_id = serializers.PrimaryKeyRelatedField(queryset=Talla.objects.all(), source='talla', write_only=True)

    class Meta:
        model = VarianteProducto
        fields = ['talla_id', 'stock', 'peso_kg', 'sku']


class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = ['id', 'nombre', 'logo', 'activa']


class CategoriaSerializer(serializers.ModelSerializer):
    imagen = serializers.ImageField(read_only=True)
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'imagen', 'imagen_url']

    def get_imagen_url(self, obj):
        if not obj.imagen:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.imagen.url) if request else obj.imagen.url


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
            'id', 'codigo', 'nombre', 'marca', 'calidad', 'precio_base', 'precio_actual',
            'en_promocion', 'disponible', 'foto_principal', 'tallas_disponibles',
        ]

    def get_foto_principal(self, obj):
        if not obj.imagen_principal:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.imagen_principal.url) if request else obj.imagen_principal.url

    def get_tallas_disponibles(self, obj):
        return [v.talla.valor for v in obj.variantes.filter(stock__gt=0)]

    def get_en_promocion(self, obj):
        return obj.promocion_vigente is not None


class ProductoDetalleSerializer(serializers.ModelSerializer):
    marca = MarcaSerializer(read_only=True)
    marca_id = serializers.PrimaryKeyRelatedField(queryset=Marca.objects.all(), source='marca', write_only=True, required=False)
    categoria = CategoriaSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), source='categoria', write_only=True, required=False
    )
    marca_options = serializers.SerializerMethodField(read_only=True)
    categoria_options = serializers.SerializerMethodField(read_only=True)
    imagen_principal = serializers.ImageField(read_only=True)
    imagenes = serializers.SerializerMethodField()
    variantes = serializers.SerializerMethodField()
    promociones = PromocionSerializer(many=True, read_only=True)
    precio_actual = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    disponible = serializers.BooleanField(read_only=True)
    variantes_input = serializers.ListField(write_only=True, required=False, child=serializers.DictField())

    class Meta:
        model = Producto
        fields = [
            'id', 'marca', 'marca_id', 'categoria', 'categoria_id', 'marca_options', 'categoria_options',
            'nombre', 'modelo', 'codigo', 'calidad', 'descripcion', 'precio_base', 'precio_actual',
            'activo', 'disponible', 'imagen_principal', 'imagenes', 'variantes', 'promociones', 'variantes_input', 'creado_en',
        ]
        read_only_fields = ['id', 'creado_en']

    def to_internal_value(self, data):
        data = data.copy()
        if 'marca' in data and 'marca_id' not in data:
            data['marca_id'] = data['marca']
        if 'categoria' in data and 'categoria_id' not in data:
            data['categoria_id'] = data['categoria']
        return super().to_internal_value(data)

    def get_marca_options(self, obj):
        return list(Marca.objects.filter(activa=True).values('id', 'nombre'))

    def get_categoria_options(self, obj):
        return list(Categoria.objects.values('id', 'nombre'))

    def get_imagenes(self, obj):
        if not obj.imagen_principal:
            return []
        request = self.context.get('request')
        url = request.build_absolute_uri(obj.imagen_principal.url) if request else obj.imagen_principal.url
        return [{'url': url}]

    def get_variantes(self, obj):
        return VarianteProductoSerializer(obj.variantes.all(), many=True, context=self.context).data

    def create(self, validated_data):
        variantes_data = validated_data.pop('variantes_input', [])
        if not variantes_data and 'variantes' in self.initial_data:
            variantes_data = self.initial_data.get('variantes', [])
        producto = Producto.objects.create(**validated_data)
        for variante_data in variantes_data:
            talla_id = variante_data.get('talla_id') or variante_data.get('talla')
            if not talla_id:
                continue
            VarianteProducto.objects.create(
                producto=producto,
                talla_id=talla_id,
                stock=variante_data.get('stock', 9999),
                peso_kg=variante_data.get('peso_kg', 0.01),
                sku=variante_data.get('sku', ''),
            )
        return producto
