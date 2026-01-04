"""
Admin configuration for financial management.
"""
from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import CostoRecurso, Presupuesto, EjecucionCosto, CicloFacturacion


@admin.register(CostoRecurso)
class CostoRecursoAdmin(BaseModelAdmin):
    list_display = ('tipo', 'descripcion', 'costo_unitario', 'unidad', 'vigencia_desde', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('descripcion',)


class EjecucionCostoInline(admin.TabularInline):
    model = EjecucionCosto
    extra = 0
    fields = ('concepto', 'tipo_recurso', 'cantidad', 'costo_unitario', 'costo_total', 'fecha')
    readonly_fields = ('costo_total',)


@admin.register(Presupuesto)
class PresupuestoAdmin(BaseModelAdmin):
    list_display = (
        'linea', 'mes', 'anio', 'estado', 'total_presupuestado',
        'total_ejecutado', 'desviacion_display'
    )
    list_filter = ('estado', 'anio', 'mes', 'linea')
    search_fields = ('linea__codigo',)
    raw_id_fields = ('linea',)
    inlines = [EjecucionCostoInline]

    fieldsets = (
        ('Período', {
            'fields': ('linea', 'mes', 'anio', 'estado')
        }),
        ('Días Hombre', {
            'fields': ('dias_hombre_planeados', 'costo_dias_hombre')
        }),
        ('Vehículos', {
            'fields': ('dias_vehiculo_planeados', 'costo_vehiculos')
        }),
        ('Otros', {
            'fields': ('viaticos_planeados', 'otros_costos')
        }),
        ('Totales', {
            'fields': ('total_presupuestado', 'total_ejecutado', 'facturacion_esperada')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
    )

    def desviacion_display(self, obj):
        desv = obj.desviacion
        if desv > 0:
            return f"+{desv:.1f}%"
        return f"{desv:.1f}%"
    desviacion_display.short_description = 'Desviación'


@admin.register(EjecucionCosto)
class EjecucionCostoAdmin(BaseModelAdmin):
    list_display = ('concepto', 'tipo_recurso', 'cantidad', 'costo_total', 'fecha', 'presupuesto')
    list_filter = ('tipo_recurso', 'fecha', 'presupuesto__linea')
    search_fields = ('concepto',)
    raw_id_fields = ('presupuesto', 'actividad')
    date_hierarchy = 'fecha'


@admin.register(CicloFacturacion)
class CicloFacturacionAdmin(BaseModelAdmin):
    list_display = (
        'presupuesto', 'estado', 'monto_facturado',
        'numero_factura', 'fecha_factura', 'dias_ciclo'
    )
    list_filter = ('estado',)
    raw_id_fields = ('presupuesto',)
