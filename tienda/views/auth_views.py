from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from tienda.serializers.usuario_serializers import (
    ConfirmarRecuperacionSerializer,
    SolicitarRecuperacionSerializer,
    UsuarioSerializer,
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
            return Response({'detail': 'IP temporalmente bloqueada por múltiples intentos fallidos.'}, status=423)

        username = request.data.get('username')
        password = request.data.get('password')
        usuario = authenticate(request, username=username, password=password)

        exitoso = usuario is not None
        registrar_intento_login(username=username or '', ip=ip, exitoso=exitoso)

        if not exitoso:
            return Response({'detail': 'Credenciales inválidas.'}, status=401)

        usuario.ultima_ip_conocida = ip
        usuario.save(update_fields=['ultima_ip_conocida'])

        refresh = RefreshToken.for_user(usuario)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'usuario': UsuarioSerializer(usuario).data,
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data['refresh'])
            token.blacklist()
        except Exception:
            return Response({'detail': 'Token inválido o ya expirado.'}, status=400)
        return Response({'detail': 'Sesión cerrada correctamente.'}, status=205)


class SolicitarRecuperacionView(APIView):
    """Pide el correo y envía un enlace con uid+token si el usuario existe (no revela si no existe)."""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'

    def post(self, request):
        from tienda.models import Usuario
        from tienda.services.email_service import notificar_recuperar_password

        serializer = SolicitarRecuperacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usuario = Usuario.objects.filter(email__iexact=serializer.validated_data['email']).first()
        if usuario:
            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = default_token_generator.make_token(usuario)
            enlace = f'{__import__("django.conf", fromlist=["settings"]).settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}'
            notificar_recuperar_password(usuario, enlace)

        return Response({'detail': 'Si el correo existe, enviamos instrucciones de recuperación.'})


class ConfirmarRecuperacionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from tienda.models import Usuario

        serializer = ConfirmarRecuperacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data

        try:
            uid = force_str(urlsafe_base64_decode(datos['uid']))
            usuario = Usuario.objects.get(pk=uid)
        except Exception:
            return Response({'detail': 'Enlace inválido.'}, status=400)

        if not default_token_generator.check_token(usuario, datos['token']):
            return Response({'detail': 'El enlace expiró o no es válido.'}, status=400)

        usuario.set_password(datos['nueva_password'])
        usuario.save(update_fields=['password'])
        return Response({'detail': 'Contraseña actualizada correctamente.'})
