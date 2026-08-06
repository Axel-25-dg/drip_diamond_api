from django.urls import path
from rest_framework.routers import DefaultRouter

from tienda.views.carrito_views import CarritoView
from tienda.views.contabilidad_views import (
    FacturaViewSet,
    LibroVentasViewSet,
    NotaCreditoViewSet,
    NotificacionViewSet,
    ReporteSRIViewSet,
    RetencionImpuestoViewSet,
)
from tienda.views.envio_views import CostoEnvioZonaViewSet
from tienda.views.imagen_views import ImagenAdjuntaViewSet, SubirImagenView
from tienda.views.pedido_views import (
    HistorialComprasView,
    PedidoViewSet,
    VerificarComprobanteView,
)
from tienda.views.producto_views import (
    CategoriaViewSet,
    MarcaViewSet,
    ProductoViewSet,
    PromocionViewSet,
    TallaViewSet,
    VarianteProductoViewSet,
)
from tienda.views.usuario_views import (
    CrearContadorView,
    CrearVendedorView,
    ListaVendedoresActivosView,
    RegistroClienteView,
    UsuarioViewSet,
    VerificarUsernameView,
)
from tienda.views.campana_views import CampanaEmailViewSet
from tienda.views.venta_views import ComisionVentaViewSet, LiquidacionMensualViewSet

router = DefaultRouter()
router.register('usuarios', UsuarioViewSet, basename='usuario')
router.register('marcas', MarcaViewSet, basename='marca')
router.register('categorias', CategoriaViewSet, basename='categoria')
router.register('tallas', TallaViewSet, basename='talla')
router.register('productos', ProductoViewSet, basename='producto')
router.register('variantes', VarianteProductoViewSet, basename='variante')
router.register('imagenes', ImagenAdjuntaViewSet, basename='imagen')
router.register('promociones', PromocionViewSet, basename='promocion')
router.register('pedidos', PedidoViewSet, basename='pedido')
router.register('costos-envio', CostoEnvioZonaViewSet, basename='costo-envio')
router.register('comisiones', ComisionVentaViewSet, basename='comision')
router.register('liquidaciones', LiquidacionMensualViewSet, basename='liquidacion')
router.register('facturas', FacturaViewSet, basename='factura')
router.register('notas-credito', NotaCreditoViewSet, basename='nota-credito')
router.register('retenciones', RetencionImpuestoViewSet, basename='retencion')
router.register('libro-ventas', LibroVentasViewSet, basename='libro-ventas')
router.register('reportes-sri', ReporteSRIViewSet, basename='reporte-sri')
router.register('notificaciones', NotificacionViewSet, basename='notificacion')
router.register('campanas', CampanaEmailViewSet, basename='campana')

urlpatterns = [
    path('imagenes/subir/', SubirImagenView.as_view(), name='subir-imagen'),

    path('usuarios/registro/', RegistroClienteView.as_view(), name='registro-cliente'),
    path('usuarios/verificar-username/', VerificarUsernameView.as_view(), name='verificar-username'),
    path('usuarios/vendedores/crear/', CrearVendedorView.as_view(), name='crear-vendedor'),
    path('usuarios/vendedores/activos/', ListaVendedoresActivosView.as_view(), name='vendedores-activos'),
    path('usuarios/contadores/crear/', CrearContadorView.as_view(), name='crear-contador'),

    path('pedidos/carrito/', CarritoView.as_view(), name='carrito'),
    path('pedidos/historial/', HistorialComprasView.as_view(), name='historial-compras'),
    path(
        'pedidos/comprobantes/<int:pk>/verificar/',
        VerificarComprobanteView.as_view({'patch': 'partial_update'}),
        name='verificar-comprobante',
    ),
] + router.urls
