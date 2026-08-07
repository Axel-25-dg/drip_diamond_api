from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from tienda.models import Categoria, Rol, Usuario


class ImagenesTests(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='Password123!',
            primer_nombre='Admin',
            primer_apellido='User',
            telefono='0991112233',
            rol=Rol.ADMINISTRADOR,
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_authenticate(user=self.admin)
        self.categoria = Categoria.objects.create(nombre='Deportivas')

    def test_subir_imagen_valida_local(self):
        image_file = BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(image_file, 'png')
        image_file.seek(0)

        uploaded = SimpleUploadedFile('test.png', image_file.read(), content_type='image/png')

        url = reverse('subir-imagen')
        data = {
            'archivo': uploaded,
            'app_label': 'tienda',
            'model': 'categoria',
            'object_id': self.categoria.id,
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('url', response.data['data'])
        self.assertIn('categorias', response.data['data']['url'])

    def test_categoria_devuelve_imagen_en_api(self):
        image_file = BytesIO()
        image = Image.new('RGB', (100, 100), color='blue')
        image.save(image_file, 'png')
        image_file.seek(0)

        uploaded = SimpleUploadedFile('categoria.png', image_file.read(), content_type='image/png')

        self.client.post(
            reverse('subir-imagen'),
            {
                'archivo': uploaded,
                'app_label': 'tienda',
                'model': 'categoria',
                'object_id': self.categoria.id,
            },
            format='multipart',
        )

        response = self.client.get(reverse('categoria-detail', kwargs={'pk': self.categoria.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('categorias', response.data['imagen'])
        self.categoria.refresh_from_db()
        self.assertTrue(self.categoria.imagen)
