from django.contrib import admin

from seguridad_acceso.models import IntentoLogin, IPBloqueada, LogAuditoria, SesionUsuario


@admin.register(IntentoLogin)
class IntentoLoginAdmin(admin.ModelAdmin):
    list_display = ['username_intentado', 'ip', 'exitoso', 'fecha']
    list_filter = ['exitoso']


@admin.register(IPBloqueada)
class IPBloqueadaAdmin(admin.ModelAdmin):
    list_display = ['ip', 'motivo', 'bloqueada_en', 'desbloquear_en']


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'accion', 'modelo_afectado', 'objeto_id', 'fecha']
    list_filter = ['modelo_afectado']


admin.site.register(SesionUsuario)
