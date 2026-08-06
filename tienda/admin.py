from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from tienda.models import (
    Carrito,
    Categoria,
    ComisionVenta,
    ComprobantePago,
    CostoEnvioZona,
    DetallePedido,
    DireccionEnvioPedido,
    Factura,
    FotoProducto,
    HistorialEstadoPedido,
    ItemCarrito,
    LibroVentas,
    LiquidacionMensual,
    Marca,
    MensajeChatPedido,
    NotaCredito,
    Notificacion,
    PerfilContador,
    PerfilVendedor,
    Pedido,
    Producto,
    Promocion,
    ReporteSRI,
    RetencionImpuesto,
    Talla,
    Usuario,
    VarianteProducto,
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['username', 'nombre_completo', 'email', 'rol', 'is_active', 'creado_en']
    list_filter = ['rol', 'is_active', 'doble_factor_activo']
    fieldsets = UserAdmin.fieldsets + (
        ('Datos de negocio', {'fields': (
            'rol', 'primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido',
            'cedula', 'telefono', 'direccion_referencial', 'doble_factor_activo',
        )}),
    )


class FotoInline(admin.TabularInline):
    model = FotoProducto
    extra = 1


class VarianteInline(admin.TabularInline):
    model = VarianteProducto
    extra = 1


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'marca', 'calidad', 'precio_base', 'activo']
    list_filter = ['marca', 'calidad', 'activo']
    search_fields = ['nombre', 'modelo']
    inlines = [VarianteInline, FotoInline]


class DetalleInline(admin.TabularInline):
    model = DetallePedido
    extra = 0


class HistorialInline(admin.TabularInline):
    model = HistorialEstadoPedido
    extra = 0
    readonly_fields = ['estado', 'comentario', 'usuario_responsable', 'fecha']


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'vendedor', 'estado', 'costo_envio_definido', 'total', 'creado_en']
    list_filter = ['estado', 'tipo_entrega', 'costo_envio_definido']
    search_fields = ['usuario__username', 'vendedor__username']
    inlines = [DetalleInline, HistorialInline]


@admin.register(ComprobantePago)
class ComprobantePagoAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'estado', 'monto_declarado', 'verificado_por', 'fecha_verificacion']
    list_filter = ['estado']


@admin.register(ComisionVenta)
class ComisionVentaAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'vendedor', 'cantidad_pares', 'monto', 'estado', 'confirmada_por']
    list_filter = ['estado']


@admin.register(LiquidacionMensual)
class LiquidacionMensualAdmin(admin.ModelAdmin):
    list_display = ['vendedor', 'periodo_mes', 'periodo_anio', 'total_comisiones', 'pagada', 'marcada_pagada_por']
    list_filter = ['pagada', 'periodo_anio']


admin.site.register(PerfilVendedor)
admin.site.register(PerfilContador)
admin.site.register(Marca)
admin.site.register(Categoria)
admin.site.register(Talla)
admin.site.register(Promocion)
admin.site.register(Carrito)
admin.site.register(ItemCarrito)
admin.site.register(DireccionEnvioPedido)
admin.site.register(CostoEnvioZona)
admin.site.register(MensajeChatPedido)
admin.site.register(Factura)
admin.site.register(NotaCredito)
admin.site.register(RetencionImpuesto)
admin.site.register(LibroVentas)
admin.site.register(ReporteSRI)
admin.site.register(Notificacion)
