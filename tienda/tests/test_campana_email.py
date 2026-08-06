from unittest.mock import patch
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from tienda.models import (
    CampanaEmail,
    EstadoCampana,
    Rol,
    SegmentoCampana,
    Usuario,
)


class CampanaEmailTests(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='Password123!',
            primer_nombre='Admin',
            primer_apellido='Master',
            telefono='0990007788',
            rol=Rol.ADMINISTRADOR,
            is_staff=True,
            is_superuser=True,
        )
        self.cliente = Usuario.objects.create_user(
            username='cliente_test',
            email='cliente@test.com',
            password='Password123!',
            primer_nombre='Juan',
            primer_apellido='Pérez',
            telefono='0991234567',
            rol=Rol.CLIENTE,
        )
        self.url_list = reverse('campana-list')

    # ── Permisos ────────────────────────────────────────────────────────────

    def test_cliente_no_puede_listar_campanas(self):
        self.client.force_authenticate(user=self.cliente)
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonimo_no_puede_listar_campanas(self):
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── CRUD ────────────────────────────────────────────────────────────────

    def test_admin_crea_campana_en_borrador(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            'titulo': 'Oferta de Verano',
            'asunto': '¡Grandes descuentos!',
            'contenido_html': '<h1>50% OFF</h1>',
            'segmento': SegmentoCampana.TODOS_LOS_CLIENTES,
        }
        response = self.client.post(self.url_list, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        campana = CampanaEmail.objects.get(titulo='Oferta de Verano')
        self.assertEqual(campana.estado, EstadoCampana.BORRADOR)
        self.assertEqual(campana.creada_por, self.admin)

    def test_admin_lista_campanas(self):
        CampanaEmail.objects.create(
            titulo='Test',
            asunto='Asunto',
            contenido_html='<p>HTML</p>',
            segmento=SegmentoCampana.VENDEDORES,
            creada_por=self.admin,
        )
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Soporta tanto respuesta paginada como sin paginar
        if 'results' in response.data:
            self.assertGreaterEqual(len(response.data['results']), 1)
        else:
            self.assertTrue(response.data['success'])
            self.assertGreaterEqual(len(response.data['data']), 1)

    def test_admin_obtiene_detalle_campana(self):
        campana = CampanaEmail.objects.create(
            titulo='Detalle',
            asunto='Asunto detalle',
            contenido_html='<p>Detalle</p>',
            segmento=SegmentoCampana.CLIENTES_CON_COMPRAS,
            creada_por=self.admin,
        )
        self.client.force_authenticate(user=self.admin)
        url = reverse('campana-detail', kwargs={'pk': campana.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['titulo'], 'Detalle')

    def test_admin_actualiza_campana_en_borrador(self):
        campana = CampanaEmail.objects.create(
            titulo='Original',
            asunto='Asunto',
            contenido_html='<p>X</p>',
            segmento=SegmentoCampana.TODOS_LOS_CLIENTES,
            creada_por=self.admin,
        )
        self.client.force_authenticate(user=self.admin)
        url = reverse('campana-detail', kwargs={'pk': campana.pk})
        response = self.client.patch(url, {'titulo': 'Actualizado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        campana.refresh_from_db()
        self.assertEqual(campana.titulo, 'Actualizado')

    def test_no_puede_editar_campana_ya_enviada(self):
        campana = CampanaEmail.objects.create(
            titulo='Enviada',
            asunto='Asunto',
            contenido_html='<p>X</p>',
            segmento=SegmentoCampana.TODOS_LOS_CLIENTES,
            estado=EstadoCampana.ENVIADO,
            creada_por=self.admin,
        )
        self.client.force_authenticate(user=self.admin)
        url = reverse('campana-detail', kwargs={'pk': campana.pk})
        response = self.client.patch(url, {'titulo': 'No deberia cambiar'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_elimina_campana_borrador(self):
        campana = CampanaEmail.objects.create(
            titulo='Para borrar',
            asunto='Asunto',
            contenido_html='<p>X</p>',
            segmento=SegmentoCampana.TODOS_LOS_CLIENTES,
            creada_por=self.admin,
        )
        self.client.force_authenticate(user=self.admin)
        url = reverse('campana-detail', kwargs={'pk': campana.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CampanaEmail.objects.filter(pk=campana.pk).exists())

    def test_no_puede_eliminar_campana_enviando(self):
        campana = CampanaEmail.objects.create(
            titulo='Enviando',
            asunto='Asunto',
            contenido_html='<p>X</p>',
            segmento=SegmentoCampana.TODOS_LOS_CLIENTES,
            estado=EstadoCampana.ENVIANDO,
            creada_por=self.admin,
        )
        self.client.force_authenticate(user=self.admin)
        url = reverse('campana-detail', kwargs={'pk': campana.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Accion: enviar ───────────────────────────────────────────────────────

    @patch('tienda.services.resend_service.enviar_correo_resend', return_value=True)
    def test_enviar_campana_borrador(self, mock_resend):
        campana = CampanaEmail.objects.create(
            titulo='Masivo',
            asunto='Asunto masivo',
            contenido_html='<p>Oferta</p>',
            segmento=SegmentoCampana.TODOS_LOS_CLIENTES,
            creada_por=self.admin,
        )
        # Hay al menos un cliente activo creado en setUp
        self.client.force_authenticate(user=self.admin)
        url = reverse('campana-enviar', kwargs={'pk': campana.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        campana.refresh_from_db()
        self.assertEqual(campana.estado, EstadoCampana.ENVIADO)
        self.assertGreater(campana.total_destinatarios, 0)

    def test_no_puede_enviar_campana_ya_enviada(self):
        campana = CampanaEmail.objects.create(
            titulo='Ya enviada',
            asunto='Asunto',
            contenido_html='<p>X</p>',
            segmento=SegmentoCampana.TODOS_LOS_CLIENTES,
            estado=EstadoCampana.ENVIADO,
            creada_por=self.admin,
        )
        self.client.force_authenticate(user=self.admin)
        url = reverse('campana-enviar', kwargs={'pk': campana.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('tienda.services.resend_service.enviar_correo_resend', return_value=False)
    def test_enviar_campana_con_todos_fallidos(self, mock_resend):
        campana = CampanaEmail.objects.create(
            titulo='Fallida',
            asunto='Asunto',
            contenido_html='<p>X</p>',
            segmento=SegmentoCampana.TODOS_LOS_CLIENTES,
            creada_por=self.admin,
        )
        self.client.force_authenticate(user=self.admin)
        url = reverse('campana-enviar', kwargs={'pk': campana.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        campana.refresh_from_db()
        self.assertEqual(campana.estado, EstadoCampana.FALLIDO)

    # ── Accion: segmentos ────────────────────────────────────────────────────

    def test_listar_segmentos_disponibles(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('campana-segmentos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        valores = [item['valor'] for item in response.data['data']]
        self.assertIn(SegmentoCampana.TODOS_LOS_CLIENTES, valores)
        self.assertIn(SegmentoCampana.VENDEDORES, valores)
