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

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'primer_nombre', 'segundo_nombre',
            'primer_apellido', 'segundo_apellido', 'nombre_completo',
            'rol', 'telefono', 'direccion_referencial',
            'doble_factor_activo', 'perfil_vendedor', 'creado_en',
        ]
        read_only_fields = ['id', 'rol', 'creado_en']

    def validate_username(self, value):
        if not username_disponible(value, usuario_actual_id=self.instance.id if self.instance else None):
            raise serializers.ValidationError('Ese nombre de usuario ya está en uso.')
        return value


class RegistroClienteSerializer(serializers.ModelSerializer):
    """
    Registro público. Pide primer/segundo nombre, primer/segundo apellido,
    correo, teléfono, dirección referencial y contraseña. El username se
    autogenera en el signal pre_save si no se envía uno.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    username = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'password', 'primer_nombre', 'segundo_nombre',
            'primer_apellido', 'segundo_apellido', 'telefono', 'direccion_referencial',
        ]

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

