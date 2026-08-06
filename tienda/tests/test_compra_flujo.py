from decimal import Decimal
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status


from tienda.models import (
    CalidadProducto,
    Carrito,
    Categoria,
    ComisionVenta,
    EstadoComprobante,
    EstadoPedido,
    ItemCarrito,
    Marca,
    Pedido,
    PerfilContador,
    PerfilVendedor,
    Producto,
    Rol,
    Talla,
    Usuario,
    VarianteProducto,
)


class FlujoCompraTests(APITestCase):
    def setUp(self):
        self.cliente = Usuario.objects.create_user(
            username='cliente_test', email='cliente@test.com', password='Password123!',
            primer_nombre='Ana', primer_apellido='Gómez', telefono='0990001122', rol=Rol.CLIENTE,
        )
        self.vendedor = Usuario.objects.create_user(
            username='vendedor_test', email='vendedor@test.com', password='Password123!',
            primer_nombre='Pedro', primer_apellido='Ramírez', telefono='0990003344', rol=Rol.VENDEDOR,
        )
        PerfilVendedor.objects.create(usuario=self.vendedor, banco='Pichincha', tipo_cuenta='Ahorros', numero_cuenta='123456')

        self.contador = Usuario.objects.create_user(
            username='contador_test', email='contador@test.com', password='Password123!',
            primer_nombre='Luis', primer_apellido='Mendoza', telefono='0990005566', rol=Rol.CONTADOR,
        )
        PerfilContador.objects.create(usuario=self.contador)

        self.admin = Usuario.objects.create_user(
            username='admin_test', email='admin@test.com', password='Password123!',
            primer_nombre='Admin', primer_apellido='Master', telefono='0990007788', rol=Rol.ADMINISTRADOR,
            is_staff=True, is_superuser=True,
        )

        self.marca = Marca.objects.create(nombre='Nike')
        self.categoria = Categoria.objects.create(nombre='Running')
        self.talla = Talla.objects.create(valor='40')
        self.producto = Producto.objects.create(
            nombre='Air Max 90', marca=self.marca, categoria=self.categoria,
            calidad=CalidadProducto.ORIGINAL, precio_base=Decimal('120.00'),
        )
        self.variante = VarianteProducto.objects.create(
            producto=self.producto, talla=self.talla, stock=10, peso_kg=Decimal('0.80'), sku='NIKE-AM90-40-BLK',
        )

    @patch('tienda.services.email_service.enviar_correo_resend', return_value=True)
    def test_flujo_compra_con_vendedor_y_comision(self, mock_email):
        # 1. Carrito
        carrito, _ = Carrito.objects.get_or_create(usuario=self.cliente)
        ItemCarrito.objects.create(carrito=carrito, variante_producto=self.variante, cantidad=1)

        # 2. Checkout eligiendo vendedor
        self.client.force_authenticate(user=self.cliente)
        url_checkout = reverse('pedido-list')
        data_checkout = {
            'vendedor_id': self.vendedor.id,
            'tipo_entrega': 'DOMICILIO',
            'direccion_formateada': 'Av. Amazonas 123 y Colón',
            'referencia_adicional': 'Frente al parque',
            'ciudad': 'Quito',
        }
        resp_checkout = self.client.post(url_checkout, data_checkout, format='json')

        self.assertEqual(resp_checkout.status_code, status.HTTP_201_CREATED)
        pedido_id = resp_checkout.data['data']['id']

        pedido = Pedido.objects.get(pk=pedido_id)
        self.assertEqual(pedido.estado, EstadoPedido.PENDIENTE_DE_PAGO)
        self.assertEqual(pedido.vendedor, self.vendedor)

        # 3. Cliente sube comprobante
        from io import BytesIO
        from PIL import Image

        img_file = BytesIO()
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(img_file, 'jpeg')
        img_file.seek(0)

        url_comprobante = reverse('pedido-subir-comprobante', kwargs={'pk': pedido_id})
        resp_comp = self.client.post(
            url_comprobante,
            {
                'archivo': SimpleUploadedFile('comp.jpg', img_file.read(), content_type='image/jpeg'),
                'banco_origen': 'Pichincha',
                'numero_referencia': 'REF12345',
                'monto_declarado': '120.00',
            },
            format='multipart',
        )

        self.assertEqual(resp_comp.status_code, status.HTTP_201_CREATED)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, EstadoPedido.COMPROBANTE_ENVIADO)

        # 4. Contador aprueba comprobante
        self.client.force_authenticate(user=self.contador)
        comprobante = pedido.comprobante_pago
        url_verificar = reverse('verificar-comprobante', kwargs={'pk': comprobante.id})
        resp_verif = self.client.patch(url_verificar, {'estado': 'VERIFICADO', 'observacion': 'OK'})
        self.assertEqual(resp_verif.status_code, status.HTTP_200_OK)

        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, EstadoPedido.PAGO_APROBADO)

        # 5. Admin despacha pedido
        self.client.force_authenticate(user=self.admin)
        url_enviar = reverse('pedido-marcar-enviado', kwargs={'pk': pedido_id})
        resp_enviar = self.client.post(url_enviar)
        self.assertEqual(resp_enviar.status_code, status.HTTP_200_OK)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, EstadoPedido.ENVIADO)

        # 6. Contador confirma entrega y se genera comisión (4 USD)
        from tienda.services.comision_service import confirmar_entrega_y_generar_comision
        comision = confirmar_entrega_y_generar_comision(pedido, self.contador)

        self.assertIsNotNone(comision)
        self.assertEqual(comision.monto, Decimal('4.00'))
        self.assertEqual(comision.vendedor, self.vendedor)

        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, EstadoPedido.ENTREGADO)

    @patch('tienda.services.email_service.enviar_correo_resend', return_value=True)
    def test_flujo_compra_ningun_vendedor_sin_comision(self, mock_email):
        carrito, _ = Carrito.objects.get_or_create(usuario=self.cliente)
        ItemCarrito.objects.create(carrito=carrito, variante_producto=self.variante, cantidad=1)

        self.client.force_authenticate(user=self.cliente)
        url_checkout = reverse('pedido-list')
        data_checkout = {
            'vendedor_id': None,  # Ningún vendedor
            'tipo_entrega': 'DOMICILIO',
            'direccion_formateada': 'Av. 9 de Octubre y Malecon',
            'ciudad': 'Guayaquil',
        }
        resp_checkout = self.client.post(url_checkout, data_checkout, format='json')

        self.assertEqual(resp_checkout.status_code, status.HTTP_201_CREATED)
        pedido_id = resp_checkout.data['data']['id']

        pedido = Pedido.objects.get(pk=pedido_id)
        self.assertIsNone(pedido.vendedor)

        # Avanzar pedido hasta enviado
        pedido.estado = EstadoPedido.ENVIADO
        pedido.save()

        # Contador confirma entrega
        from tienda.services.comision_service import confirmar_entrega_y_generar_comision
        comision = confirmar_entrega_y_generar_comision(pedido, self.contador)

        self.assertIsNone(comision)
        self.assertFalse(ComisionVenta.objects.filter(pedido=pedido).exists())
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, EstadoPedido.ENTREGADO)
