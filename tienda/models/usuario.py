from django.contrib.auth.models import AbstractUser
from django.db import models


class Rol(models.TextChoices):
    ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'
    CONTADOR = 'CONTADOR', 'Contador'
    VENDEDOR = 'VENDEDOR', 'Vendedor'
    CLIENTE = 'CLIENTE', 'Usuario normal'


class Usuario(AbstractUser):
    """
    Usuario base. El username se autogenera a partir de los nombres
    (ver tienda/services/username_service.py) pero queda editable
    siempre que se mantenga único.
    """
    primer_nombre = models.CharField(max_length=50)
    segundo_nombre = models.CharField(max_length=50, blank=True)
    primer_apellido = models.CharField(max_length=50)
    segundo_apellido = models.CharField(max_length=50, blank=True)

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.CLIENTE)
    telefono = models.CharField(max_length=15)
    direccion_referencial = models.CharField(
        max_length=255, blank=True,
        help_text='Dirección de referencia del registro; la dirección exacta se pide en cada compra.',
    )
    foto_perfil = models.ImageField(upload_to='usuarios/perfiles/', blank=True, null=True)

    doble_factor_activo = models.BooleanField(default=False)
    ultima_ip_conocida = models.GenericIPAddressField(null=True, blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        indexes = [models.Index(fields=['rol'])]

    def __str__(self):
        return f'{self.nombre_completo} ({self.get_rol_display()})'

    @property
    def nombre_completo(self):
        partes = [self.primer_nombre, self.segundo_nombre, self.primer_apellido, self.segundo_apellido]
        return ' '.join(p for p in partes if p)

    @property
    def es_administrador(self):
        return self.rol == Rol.ADMINISTRADOR

    @property
    def es_contador(self):
        return self.rol == Rol.CONTADOR

    @property
    def es_vendedor(self):
        return self.rol == Rol.VENDEDOR

    @property
    def es_cliente(self):
        return self.rol == Rol.CLIENTE
