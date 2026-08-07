from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tienda.models import Categoria, Marca, Producto, Rol, Talla, Usuario


class ProductoApiTests(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username='admin_productos',
            email='admin-productos@test.com',
            password='Password123!',
            primer_nombre='Admin',
            primer_apellido='Productos',
            telefono='0991112234',
            rol=Rol.ADMINISTRADOR,
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_authenticate(user=self.admin)
        self.marca = Marca.objects.create(nombre='Nike')
        self.categoria = Categoria.objects.create(nombre='Running')
        self.talla = Talla.objects.create(valor='39')

    def test_crear_producto_con_codigo_y_variantes(self):
        response = self.client.post(
            reverse('producto-list'),
            {
                'nombre': 'Air Max',
                'marca_id': self.marca.id,
                'categoria_id': self.categoria.id,
                'precio_base': '120.00',
                'codigo': 'ZAP-1001',
                'variantes': [
                    {
                        'talla_id': self.talla.id,
                        'stock': 10,
                        'peso_kg': '0.30',
                        'sku': 'ZAP-1001-39',
                    }
                ],
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        producto = Producto.objects.get(codigo='ZAP-1001')
        self.assertEqual(producto.variantes.count(), 1)
        self.assertEqual(producto.variantes.first().talla.valor, '39')

    def test_crear_producto_con_aliases_de_marca_y_categoria(self):
        response = self.client.post(
            reverse('producto-list'),
            {
                'nombre': 'Pegasus',
                'marca': self.marca.id,
                'categoria': self.categoria.id,
                'precio_base': '99.00',
                'codigo': 'ZAP-1002',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        producto = Producto.objects.get(codigo='ZAP-1002')
        self.assertEqual(producto.marca_id, self.marca.id)
        self.assertEqual(producto.categoria_id, self.categoria.id)

    def test_crear_producto_sin_codigo_lo_genera_automaticamente(self):
        response = self.client.post(
            reverse('producto-list'),
            {
                'nombre': 'Jordan',
                'marca': self.marca.id,
                'categoria': self.categoria.id,
                'precio_base': '150.00',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        producto = Producto.objects.get(id=response.data['id'])
        self.assertTrue(producto.codigo)
        self.assertTrue(producto.codigo.startswith('ZAP-'))


class CampanaEnvioTests(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username='admin_campanas',
            email='admin-campanas@test.com',
            password='Password123!',
            primer_nombre='Admin',
            primer_apellido='Campanas',
            telefono='0992223344',
            rol=Rol.ADMINISTRADOR,
            is_staff=True,
            is_superuser=True,
        )
        self.vendedor = Usuario.objects.create_user(
            username='vendedor_test',
            email='vendedor@test.com',
            password='Password123!',
            primer_nombre='Vendedor',
            primer_apellido='Test',
            telefono='0993334455',
            rol=Rol.VENDEDOR,
        )
        self.contador = Usuario.objects.create_user(
            username='contador_test',
            email='contador@test.com',
            password='Password123!',
            primer_nombre='Contador',
            primer_apellido='Test',
            telefono='0994445566',
            rol=Rol.CONTADOR,
        )
        self.cliente = Usuario.objects.create_user(
            username='cliente_campana',
            email='cliente-campana@test.com',
            password='Password123!',
            primer_nombre='Cliente',
            primer_apellido='Campana',
            telefono='0995556677',
            rol=Rol.CLIENTE,
        )

    @patch('tienda.services.resend_service.enviar_correo_resend', return_value=True)
    def test_envio_masivo_para_vendedores_y_contadores(self, mock_send):
        from tienda.services.campana_service import enviar_campana
        from tienda.models import CampanaEmail, SegmentoCampana

        campana = CampanaEmail.objects.create(
            titulo='Prueba segmentos',
            asunto='Asunto prueba',
            contenido_html='<p>Hola</p>',
            segmento=SegmentoCampana.VENDEDORES,
            creada_por=self.admin,
        )
        resultado = enviar_campana(campana.id)

        self.assertEqual(resultado['enviados'], 1)
        self.assertEqual(resultado['fallidos'], 0)
        self.assertEqual(mock_send.call_count, 1)
        self.assertEqual(mock_send.call_args.kwargs['destinatario'], self.vendedor.email)

        campana_contadores = CampanaEmail.objects.create(
            titulo='Prueba contadores',
            asunto='Asunto prueba',
            contenido_html='<p>Hola</p>',
            segmento=SegmentoCampana.CONTADORES,
            creada_por=self.admin,
        )
        resultado2 = enviar_campana(campana_contadores.id)

        self.assertEqual(resultado2['enviados'], 1)
        self.assertEqual(mock_send.call_args_list[-1].kwargs['destinatario'], self.contador.email)
