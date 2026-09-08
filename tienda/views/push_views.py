from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.views import APIView

from core.responses import error_response, success_response
from tienda.models import SuscripcionPush, CampanaNotificacionPush, Usuario
from tienda.permissions import EsAdministrador
from tienda.serializers.push_serializers import (
    CampanaNotificacionPushSerializer,
    DesuscribirPushSerializer,
    EnviarPushCustomAdminSerializer,
    RegistrarSuscripcionPushSerializer,
    SuscripcionPushSerializer,
)
from tienda.services.push_service import broadcast_push_campana, enviar_notificacion_push_suscripcion
from tienda.utils.vapid_utils import obtener_o_generar_llaves_vapid


class VapidPublicKeyView(APIView):
    """
    Entrega la clave pública VAPID para que el navegador/sistema cliente
    pueda suscribirse a las notificaciones Push nativas.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        public_key, _, claim_email = obtener_o_generar_llaves_vapid()
        return success_response(
            data={
                'vapid_public_key': public_key,
                'claim_email': claim_email,
            },
            message='Llave pública VAPID obtenida exitosamente.'
        )


class SuscribirPushView(APIView):
    """
    Registra o actualiza la suscripción del navegador/dispositivo actual del usuario.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistrarSuscripcionPushSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        endpoint = serializer.validated_data['endpoint']
        keys = serializer.validated_data['keys']
        user_agent = serializer.validated_data.get('user_agent', request.META.get('HTTP_USER_AGENT', ''))
        usuario = request.user if request.user and request.user.is_authenticated else None

        suscripcion, creada = SuscripcionPush.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'usuario': usuario,
                'p256dh': keys['p256dh'],
                'auth': keys['auth'],
                'user_agent': user_agent,
                'activa': True,
                'ip_registro': request.META.get('REMOTE_ADDR'),
            }
        )

        # Enviar notificación de bienvenida/prueba nativa al sistema
        enviar_notificacion_push_suscripcion(
            suscripcion=suscripcion,
            titulo="¡Notificaciones Nativas Activadas! 🔔",
            cuerpo="Recibirás alertas de tus pedidos y promociones exclusivas en tu pantalla.",
            url_destino="/",
            data={'tipo': 'BIENVENIDA_PUSH'}
        )

        return success_response(
            data=SuscripcionPushSerializer(suscripcion).data,
            message='Suscripción a notificaciones push registrada correctamente.',
            status=status.HTTP_201_CREATED if creada else status.HTTP_200_OK
        )


class DesuscribirPushView(APIView):
    """
    Desactiva la suscripción Push para un endpoint específico.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = DesuscribirPushSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        endpoint = serializer.validated_data['endpoint']
        updated = SuscripcionPush.objects.filter(endpoint=endpoint).update(activa=False)

        return success_response(
            data={'desuscritos': updated},
            message='Suscripción push desactivada exitosamente.'
        )


class AdminPushNotificationViewSet(viewsets.ModelViewSet):
    """
    API de administración para gestionar, redactar y enviar notificaciones
    masivas y personalizadas a la barra del sistema operativo de los usuarios.
    """
    queryset = CampanaNotificacionPush.objects.select_related('creado_por').prefetch_related('usuarios_especificos').all()
    serializer_class = CampanaNotificacionPushSerializer
    permission_classes = [EsAdministrador]

    @action(detail=False, methods=['post'], url_path='enviar-custom')
    def enviar_custom(self, request):
        """
        Envía una notificación personalizada redactada por un Administrador
        con opción de vista previa en tiempo real y filtrado de usuarios.
        """
        serializer = EnviarPushCustomAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        campana = CampanaNotificacionPush.objects.create(
            titulo=data['titulo'],
            cuerpo=data['cuerpo'],
            icono_url=data.get('icono_url', ''),
            imagen_url=data.get('imagen_url', ''),
            url_destino=data.get('url_destino', '/'),
            badge_url=data.get('badge_url', ''),
            sonido_activo=data.get('sonido_activo', True),
            vibracion_activa=data.get('vibracion_activa', True),
            segmento=data['segmento'],
            creado_por=request.user
        )

        if data['segmento'] == 'ESPECIFICOS' and data.get('usuarios_ids'):
            usuarios = Usuario.objects.filter(id__in=data['usuarios_ids'])
            campana.usuarios_especificos.set(usuarios)

        res = broadcast_push_campana(campana)

        return success_response(
            data={
                'campana': CampanaNotificacionPushSerializer(campana).data,
                'resultado': res
            },
            message=f"Notificación despachada: {res['exitosos']} entregadas exitosamente de {res['total']} dispositivos.",
            status=status.HTTP_201_CREATED
        )
