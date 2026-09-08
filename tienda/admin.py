from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from tienda.models import (
    CampanaEmail,
    CampanaNotificacionPush,
    Carrito,
    Categoria,
    ComisionVenta,
    ComprobantePago,
    CostoEnvioZona,
    DetallePedido,
    DireccionEnvioPedido,
    Factura,
    HistorialEstadoPedido,
    ItemCarrito,
    LibroVentas,
    LiquidacionMensual,
    Marca,
    NotaCredito,
    Notificacion,
    PerfilContador,
    PerfilVendedor,
    Pedido,
    Producto,
    Promocion,
    ReporteSRI,
    RetencionImpuesto,
    SuscripcionPush,
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
            'telefono', 'direccion_referencial', 'doble_factor_activo',
        )}),
    )


class VarianteInline(admin.TabularInline):
    model = VarianteProducto
    extra = 1


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'marca', 'calidad', 'precio_base', 'activo']
    list_filter = ['marca', 'calidad', 'activo']
    search_fields = ['nombre', 'modelo']
    inlines = [VarianteInline]


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
admin.site.register(Factura)
admin.site.register(NotaCredito)
admin.site.register(RetencionImpuesto)
admin.site.register(LibroVentas)
admin.site.register(ReporteSRI)
admin.site.register(Notificacion)


@admin.register(CampanaEmail)
class CampanaEmailAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'segmento', 'estado', 'total_destinatarios', 'total_enviados', 'total_fallidos', 'creada_por', 'creada_en']
    list_filter = ['estado', 'segmento']
    search_fields = ['titulo', 'asunto']
    readonly_fields = ['total_destinatarios', 'total_enviados', 'total_fallidos', 'creada_en', 'enviada_en']
    actions = ['enviar_campanas_accion']

    @admin.action(description='🚀 Enviar campaña(s) masiva(s) seleccionada(s)')
    def enviar_campanas_accion(self, request, queryset):
        from tienda.services.campana_service import enviar_campana
        from tienda.models import EstadoCampana

        procesados = 0
        for campana in queryset:
            if campana.estado in (EstadoCampana.BORRADOR, EstadoCampana.FALLIDO):
                res = enviar_campana(campana.id)
                if 'error' not in res:
                    procesados += 1
        self.message_user(request, f'Se ejecutó el envío de {procesados} campaña(s) masiva(s).')


@admin.register(SuscripcionPush)
class SuscripcionPushAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'endpoint_corto', 'activa', 'user_agent_corto', 'creada_en', 'ultima_actividad']
    list_filter = ['activa', 'creada_en']
    search_fields = ['usuario__username', 'usuario__email', 'endpoint']
    readonly_fields = ['creada_en', 'ultima_actividad']
    actions = ['probar_notificacion_push_accion']

    def endpoint_corto(self, obj):
        return f"{obj.endpoint[:45]}..."
    endpoint_corto.short_description = 'Endpoint Push'

    def user_agent_corto(self, obj):
        return obj.user_agent[:35] if obj.user_agent else '-'
    user_agent_corto.short_description = 'Navegador/SO'

    @admin.action(description='🔔 Enviar Notificación Push de Prueba al Dispositivo')
    def probar_notificacion_push_accion(self, request, queryset):
        from tienda.services.push_service import enviar_notificacion_push_suscripcion
        exitosos = 0
        for sub in queryset:
            ok = enviar_notificacion_push_suscripcion(
                suscripcion=sub,
                titulo="¡Prueba de Notificación Push! 🔔",
                cuerpo="Esta es una prueba de notificación nativa enviada desde Django Admin.",
                url_destino="/"
            )
            if ok:
                exitosos += 1
        self.message_user(request, f'Notificación Push enviada con éxito a {exitosos} dispositivo(s).')


@admin.register(CampanaNotificacionPush)
class CampanaNotificacionPushAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'segmento', 'total_enviados', 'total_exitosos', 'total_fallidos', 'creado_por', 'creada_en']
    list_filter = ['segmento', 'creada_en']
    search_fields = ['titulo', 'cuerpo']
    readonly_fields = ['total_enviados', 'total_exitosos', 'total_fallidos', 'creada_en']
    actions = ['despachar_push_masivo_accion']

    @admin.action(description='🚀 Despachar Notificación Push Masiva a la Barra del Sistema')
    def despachar_push_masivo_accion(self, request, queryset):
        from tienda.services.push_service import broadcast_push_campana
        for campana in queryset:
            broadcast_push_campana(campana)
        self.message_user(request, f'Se despacharon {queryset.count()} campaña(s) Push nativas al sistema.')



