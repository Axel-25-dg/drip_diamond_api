from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken, BlacklistedToken

from core.responses import error_response, success_response
from seguridad_acceso.models import CodigoOTP
from tienda.serializers.usuario_serializers import (
    ConfirmarRecuperacionSerializer,
    SolicitarRecuperacionSerializer,
    UsuarioSerializer,
    VerificarOTPSerializer,
)


def _obtener_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        from seguridad_acceso.services import ip_esta_bloqueada, registrar_intento_login

        ip = _obtener_ip(request)
        if ip_esta_bloqueada(ip):
            return error_response(
                message='IP temporalmente bloqueada por múltiples intentos fallidos.',
                status=423,
            )

        username = request.data.get('username')
        password = request.data.get('password')
        usuario = authenticate(request, username=username, password=password)

        exitoso = usuario is not None
        registrar_intento_login(username=username or '', ip=ip, exitoso=exitoso)

        if not exitoso:
            return error_response(message='Credenciales inválidas.', status=401)

        usuario.ultima_ip_conocida = ip
        usuario.save(update_fields=['ultima_ip_conocida'])

        refresh = RefreshToken.for_user(usuario)
        return success_response(
            data={
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'usuario': UsuarioSerializer(usuario).data,
            },
            message='Inicio de sesión exitoso.',
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token_str = request.data.get('refresh')
            if token_str:
                token = RefreshToken(token_str)
                token.blacklist()
        except Exception:
            pass
        return success_response(message='Sesión cerrada correctamente.')


class SolicitarRecuperacionView(APIView):
    """
    Paso 1: Solicitar código OTP de 6 dígitos enviado por correo mediante Resend.
    Expira en 10 minutos.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        from tienda.models import Usuario
        from tienda.services.email_service import notificar_codigo_otp

        serializer = SolicitarRecuperacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        usuario = Usuario.objects.filter(email__iexact=email).first()

        if usuario:
            otp = CodigoOTP.generar_para_usuario(usuario)
            notificar_codigo_otp(usuario, otp.codigo)

        return success_response(
            data={'email': email},
            message='Si el correo se encuentra registrado, se enviará un código OTP de 6 dígitos.',
        )


class VerificarOTPView(APIView):
    """
    Paso 2: Verificar el código OTP de 6 dígitos (Máximo 5 intentos, 10 min de validez).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from tienda.models import Usuario

        serializer = VerificarOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        usuario = Usuario.objects.filter(email__iexact=datos['email']).first()
        if not usuario:
            return error_response(message='Código OTP inválido o expirado.', status=400)

        otp = CodigoOTP.objects.filter(usuario=usuario, usado=False).order_by('-creado_en').first()
        if not otp:
            return error_response(message='No hay ningún código OTP activo para este correo.', status=400)

        if otp.esta_expirado:
            return error_response(message='El código OTP ha expirado (validez: 10 minutos). Solicite uno nuevo.', status=400)

        if otp.excede_intentos:
            return error_response(message='Ha superado el límite de 5 intentos. Solicite un nuevo código OTP.', status=400)

        if otp.codigo != datos['codigo']:
            otp.intentos += 1
            otp.save(update_fields=['intentos'])
            intentos_restantes = 5 - otp.intentos
            return error_response(
                message=f'Código OTP incorrecto. Le quedan {intentos_restantes} intentos.',
                status=400,
            )

        otp.verificado = True
        otp.save(update_fields=['verificado'])
        return success_response(
            data={'email': datos['email'], 'codigo': datos['codigo']},
            message='Código OTP verificado correctamente. Ya puede establecer su nueva contraseña.',
        )


class ConfirmarRecuperacionView(APIView):
    """
    Paso 3: Establecer nueva contraseña con OTP verificado.
    Invalida automáticamente todas las sesiones anteriores.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from tienda.models import Usuario

        serializer = ConfirmarRecuperacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        usuario = Usuario.objects.filter(email__iexact=datos['email']).first()
        if not usuario:
            return error_response(message='Solicitud inválida.', status=400)

        otp = CodigoOTP.objects.filter(
            usuario=usuario, codigo=datos['codigo'], verificado=True, usado=False
        ).order_by('-creado_en').first()

        if not otp or otp.esta_expirado:
            return error_response(message='El código OTP no fue verificado o ya ha expirado.', status=400)

        # Actualizar contraseña
        usuario.set_password(datos['nueva_password'])
        usuario.save(update_fields=['password'])

        # Marcar OTP como usado
        otp.usado = True
        otp.save(update_fields=['usado'])

        # Involucrar invalidación de todas las sesiones anteriores (simplejwt tokens blacklist)
        try:
            tokens = OutstandingToken.objects.filter(user=usuario)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            pass

        return success_response(
            data={},
            message='Contraseña actualizada correctamente. Todas las sesiones anteriores fueron cerradas.',
        )
