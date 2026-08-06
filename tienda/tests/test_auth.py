from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from seguridad_acceso.models import CodigoOTP
from tienda.models import Rol, Usuario


class AuthTests(APITestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            username='cliente_test',
            email='cliente@test.com',
            password='Password123!',
            primer_nombre='Juan',
            primer_apellido='Pérez',
            telefono='0991234567',
            rol=Rol.CLIENTE,
        )

    def test_login_exitoso(self):
        url = reverse('login')
        data = {'username': 'cliente_test', 'password': 'Password123!'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])

    @patch('tienda.services.email_service.enviar_correo_resend', return_value=True)
    def test_registro_cliente_sin_cedula(self, mock_email):
        url = reverse('registro-cliente')
        data = {
            'email': 'nuevo@test.com',
            'password': 'Password123!',
            'primer_nombre': 'Carlos',
            'primer_apellido': 'López',
            'telefono': '0987654321',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertTrue(Usuario.objects.filter(email='nuevo@test.com').exists())

    @patch('tienda.services.email_service.enviar_correo_resend', return_value=True)
    def test_recuperacion_password_otp_flujo_completo(self, mock_email):
        # 1. Solicitar OTP
        url_solicitar = reverse('recuperar-password')
        resp1 = self.client.post(url_solicitar, {'email': 'cliente@test.com'})
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)
        self.assertTrue(resp1.data['success'])

        otp = CodigoOTP.objects.filter(usuario=self.cliente, usado=False).first()
        self.assertIsNotNone(otp)
        self.assertEqual(len(otp.codigo), 6)

        # 2. Verificar OTP
        url_verificar = reverse('verificar-otp')
        resp2 = self.client.post(url_verificar, {'email': 'cliente@test.com', 'codigo': otp.codigo})
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertTrue(resp2.data['success'])

        # 3. Confirmar nueva contraseña
        url_confirmar = reverse('confirmar-password')
        resp3 = self.client.post(
            url_confirmar,
            {'email': 'cliente@test.com', 'codigo': otp.codigo, 'nueva_password': 'NuevaPassword123!'},
        )
        self.assertEqual(resp3.status_code, status.HTTP_200_OK)
        self.assertTrue(resp3.data['success'])

        # Verificar que la nueva contraseña funciona
        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.check_password('NuevaPassword123!'))
