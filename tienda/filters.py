import django_filters

from tienda.models import Producto


class ProductoFilter(django_filters.FilterSet):
    precio_min = django_filters.NumberFilter(field_name='precio_base', lookup_expr='gte')
    precio_max = django_filters.NumberFilter(field_name='precio_base', lookup_expr='lte')
    talla = django_filters.CharFilter(field_name='variantes__talla__valor', lookup_expr='iexact')
    codigo = django_filters.CharFilter(field_name='codigo', lookup_expr='icontains')

    class Meta:
        model = Producto
        fields = ['marca', 'categoria', 'calidad', 'precio_min', 'precio_max', 'talla', 'codigo']
