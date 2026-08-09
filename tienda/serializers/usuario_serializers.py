from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from tienda.models import PerfilContador, PerfilVendedor, Rol, Usuario
from tienda.services.username_service import username_disponible


class PerfilVendedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilVendedor
        fields = ['codigo_vendedor', 'activo', 'banco', 'tipo_cuenta', 'numero_cuenta']
        read_only_fields = ['codigo_vendedor']


class UsuarioSerializer(serializers.ModelSerializer):
    perfil_vendedor = PerfilVendedorSerializer(read_only=True)
    nombre_completo = serializers.CharField(read_only=True)

    # Alias para compatibilidad con el frontend
    correo = serializers.EmailField(source='email', required=False)
    nombre = serializers.CharField(source='primer_nombre', required=False)
    apellido = serializers.CharField(source='primer_apellido', required=False)
    foto_perfil = serializers.ImageField(required=False, allow_null=True)
    foto_perfil_url = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'correo',
            'primer_nombre', 'segundo_nombre',
            'primer_apellido', 'segundo_apellido',
            'nombre', 'apellido',
            'nombre_completo', 'rol', 'telefono',
            'direccion_referencial', 'doble_factor_activo',
            'perfil_vendedor', 'creado_en',
            'foto_perfil', 'foto_perfil_url',
        ]
        read_only_fields = ['id', 'rol', 'creado_en']

    def get_foto_perfil_url(self, obj):
        if not obj.foto_perfil:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.foto_perfil.url)
        return obj.foto_perfil.url

    def to_internal_value(self, data):
        data = data.copy()
        if 'correo' in data and 'email' not in data:
            data['email'] = data.pop('correo')
        if 'nombre' in data and 'primer_nombre' not in data:
            data['primer_nombre'] = data.pop('nombre')
        if 'apellido' in data and 'primer_apellido' not in data:
            data['primer_apellido'] = data.pop('apellido')
        return super().to_internal_value(data)

    def validate_username(self, value):
        if not username_disponible(value, usuario_actual_id=self.instance.id if self.instance else None):
            raise serializers.ValidationError('Ese nombre de usuario ya está en uso.')
        return value



class RegistroClienteSerializer(serializers.ModelSerializer):
    """
    Registro público. Acepta tanto los campos del frontend (correo, nombre, apellido)
    como los nativos (email, primer_nombre, primer_apellido). El username se
    autogenera si no se envía uno.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    username = serializers.CharField(required=False, allow_blank=True, default='')

    correo = serializers.EmailField(write_only=True, required=False)
    nombre = serializers.CharField(write_only=True, required=False)
    apellido = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'correo', 'password',
            'primer_nombre', 'nombre', 'segundo_nombre',
            'primer_apellido', 'apellido', 'segundo_apellido',
            'telefono', 'direccion_referencial',
        ]
        extra_kwargs = {
            'email': {'required': False},
            'primer_nombre': {'required': False},
            'primer_apellido': {'required': False},
            'telefono': {'required': False, 'allow_blank': True},
        }

    def validate(self, attrs):
        if 'correo' in attrs and not attrs.get('email'):
            attrs['email'] = attrs.pop('correo')
        elif 'correo' in attrs:
            attrs.pop('correo')

        if 'nombre' in attrs and not attrs.get('primer_nombre'):
            attrs['primer_nombre'] = attrs.pop('nombre')
        elif 'nombre' in attrs:
            attrs.pop('nombre')

        if 'apellido' in attrs and not attrs.get('primer_apellido'):
            attrs['primer_apellido'] = attrs.pop('apellido')
        elif 'apellido' in attrs:
            attrs.pop('apellido')

        if not attrs.get('email'):
            raise serializers.ValidationError({'correo': 'El correo electrónico es obligatorio.'})
        if not attrs.get('primer_nombre'):
            raise serializers.ValidationError({'nombre': 'El nombre es obligatorio.'})
        if not attrs.get('primer_apellido'):
            raise serializers.ValidationError({'apellido': 'El apellido es obligatorio.'})

        return attrs

    def validate_username(self, value):
        if value and not username_disponible(value):
            raise serializers.ValidationError('Ese nombre de usuario ya está en uso.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        username = validated_data.pop('username', '') or ''
        usuario = Usuario(rol=Rol.CLIENTE, username=username, **validated_data)
        usuario.set_password(password)
        usuario.save()
        return usuario



class CrearVendedorSerializer(serializers.ModelSerializer):
    """Solo el administrador crea vendedores. Requiere datos de pago para la liquidación mensual."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    banco = serializers.CharField(write_only=True, required=False, allow_blank=True)
    tipo_cuenta = serializers.CharField(write_only=True, required=False, allow_blank=True)
    numero_cuenta = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'password', 'primer_nombre', 'segundo_nombre',
            'primer_apellido', 'segundo_apellido', 'telefono',
            'banco', 'tipo_cuenta', 'numero_cuenta',
        ]

    def create(self, validated_data):
        banco = validated_data.pop('banco', '')
        tipo_cuenta = validated_data.pop('tipo_cuenta', '')
        numero_cuenta = validated_data.pop('numero_cuenta', '')
        password = validated_data.pop('password')

        usuario = Usuario(rol=Rol.VENDEDOR, **validated_data)
        usuario.set_password(password)
        usuario.save()
        PerfilVendedor.objects.create(
            usuario=usuario, banco=banco, tipo_cuenta=tipo_cuenta, numero_cuenta=numero_cuenta,
        )
        return usuario


class CrearContadorSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'password', 'primer_nombre', 'segundo_nombre',
            'primer_apellido', 'segundo_apellido', 'telefono',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        usuario = Usuario(rol=Rol.CONTADOR, **validated_data)
        usuario.set_password(password)
        usuario.save()
        PerfilContador.objects.create(usuario=usuario)
        return usuario


class SolicitarRecuperacionSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerificarOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    codigo = serializers.CharField(max_length=6, min_length=6)


class ConfirmarRecuperacionSerializer(serializers.Serializer):
    email = serializers.EmailField()
    codigo = serializers.CharField(max_length=6, min_length=6)
    nueva_password = serializers.CharField(validators=[validate_password])

