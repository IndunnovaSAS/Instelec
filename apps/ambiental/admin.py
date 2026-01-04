"""
Admin configuration for environmental management.
"""
from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import InformeAmbiental, PermisoServidumbre


@admin.register(InformeAmbiental)
class InformeAmbientalAdmin(BaseModelAdmin):
    list_display = (
        'linea', 'periodo_mes', 'periodo_anio', 'estado',
        'total_actividades', 'elaborado_por', 'fecha_envio'
    )
    list_filter = ('estado', 'periodo_anio', 'periodo_mes', 'linea')
    search_fields = ('linea__codigo', 'linea__nombre')
    raw_id_fields = ('linea', 'elaborado_por', 'revisado_por', 'aprobado_por')

    fieldsets = (
        ('Período', {
            'fields': ('linea', 'periodo_mes', 'periodo_anio')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Resumen', {
            'fields': ('total_actividades', 'total_podas', 'hectareas_intervenidas', 'm3_vegetacion')
        }),
        ('Workflow', {
            'fields': (
                ('elaborado_por', 'fecha_elaboracion'),
                ('revisado_por', 'fecha_revision'),
                ('aprobado_por', 'fecha_aprobacion'),
                'fecha_envio'
            )
        }),
        ('Archivos', {
            'fields': ('url_pdf', 'url_excel')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
    )


@admin.register(PermisoServidumbre)
class PermisoServidumbreAdmin(BaseModelAdmin):
    list_display = (
        'torre', 'propietario_nombre', 'predio_nombre',
        'fecha_autorizacion', 'fecha_vencimiento', 'vigente'
    )
    list_filter = ('fecha_autorizacion', 'torre__linea')
    search_fields = ('propietario_nombre', 'predio_nombre', 'torre__numero')
    raw_id_fields = ('torre',)

    def vigente(self, obj):
        return obj.vigente
    vigente.boolean = True
    vigente.short_description = 'Vigente'
