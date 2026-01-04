"""
Admin configuration for activities.
"""
from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import TipoActividad, ProgramacionMensual, Actividad


@admin.register(TipoActividad)
class TipoActividadAdmin(BaseModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'tiempo_estimado_horas', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('codigo', 'nombre')

    fieldsets = (
        (None, {
            'fields': ('codigo', 'nombre', 'categoria', 'descripcion')
        }),
        ('Requisitos de fotos', {
            'fields': ('requiere_fotos_antes', 'requiere_fotos_durante', 'requiere_fotos_despues', 'min_fotos')
        }),
        ('Configuración', {
            'fields': ('campos_formulario', 'tiempo_estimado_horas', 'activo')
        }),
    )


@admin.register(ProgramacionMensual)
class ProgramacionMensualAdmin(BaseModelAdmin):
    list_display = ('linea', 'mes', 'anio', 'total_actividades', 'aprobado', 'aprobado_por')
    list_filter = ('anio', 'mes', 'linea', 'aprobado')
    search_fields = ('linea__codigo', 'linea__nombre')
    raw_id_fields = ('linea', 'aprobado_por')
    readonly_fields = ('total_actividades',)


@admin.register(Actividad)
class ActividadAdmin(BaseModelAdmin):
    list_display = (
        'tipo_actividad', 'torre', 'linea', 'cuadrilla',
        'fecha_programada', 'estado', 'prioridad'
    )
    list_filter = ('estado', 'prioridad', 'linea', 'tipo_actividad', 'fecha_programada')
    search_fields = ('torre__numero', 'linea__codigo', 'cuadrilla__codigo')
    raw_id_fields = ('linea', 'torre', 'tipo_actividad', 'cuadrilla', 'programacion')
    date_hierarchy = 'fecha_programada'

    fieldsets = (
        (None, {
            'fields': ('linea', 'torre', 'tipo_actividad')
        }),
        ('Programación', {
            'fields': ('cuadrilla', 'fecha_programada', 'hora_inicio_estimada', 'programacion')
        }),
        ('Estado', {
            'fields': ('estado', 'prioridad')
        }),
        ('Reprogramación', {
            'fields': ('fecha_reprogramada', 'motivo_reprogramacion'),
            'classes': ('collapse',)
        }),
        ('Cancelación', {
            'fields': ('motivo_cancelacion',),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': ('observaciones_programacion',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'linea', 'torre', 'tipo_actividad', 'cuadrilla'
        )
