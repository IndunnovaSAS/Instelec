"""
Admin configuration for crews.
"""
from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import Vehiculo, Cuadrilla, CuadrillaMiembro, TrackingUbicacion


class CuadrillaMiembroInline(admin.TabularInline):
    model = CuadrillaMiembro
    extra = 0
    fields = ('usuario', 'rol_cuadrilla', 'fecha_inicio', 'fecha_fin', 'activo')
    raw_id_fields = ('usuario',)


@admin.register(Vehiculo)
class VehiculoAdmin(BaseModelAdmin):
    list_display = ('placa', 'tipo', 'marca', 'modelo', 'ano', 'costo_dia', 'activo')
    list_filter = ('tipo', 'activo', 'marca')
    search_fields = ('placa', 'marca', 'modelo')


@admin.register(Cuadrilla)
class CuadrillaAdmin(BaseModelAdmin):
    list_display = ('codigo', 'nombre', 'supervisor', 'vehiculo', 'linea_asignada', 'total_miembros', 'activa')
    list_filter = ('activa', 'linea_asignada')
    search_fields = ('codigo', 'nombre', 'supervisor__first_name', 'supervisor__last_name')
    raw_id_fields = ('supervisor', 'vehiculo', 'linea_asignada')
    inlines = [CuadrillaMiembroInline]

    fieldsets = (
        (None, {
            'fields': ('codigo', 'nombre', 'activa')
        }),
        ('Asignaciones', {
            'fields': ('supervisor', 'vehiculo', 'linea_asignada')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
    )


@admin.register(CuadrillaMiembro)
class CuadrillaMiembroAdmin(BaseModelAdmin):
    list_display = ('usuario', 'cuadrilla', 'rol_cuadrilla', 'fecha_inicio', 'fecha_fin', 'activo')
    list_filter = ('cuadrilla', 'rol_cuadrilla', 'activo')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'cuadrilla__codigo')
    raw_id_fields = ('cuadrilla', 'usuario')


@admin.register(TrackingUbicacion)
class TrackingUbicacionAdmin(admin.ModelAdmin):
    list_display = ('cuadrilla', 'usuario', 'latitud', 'longitud', 'precision_metros', 'created_at')
    list_filter = ('cuadrilla', 'created_at')
    search_fields = ('cuadrilla__codigo', 'usuario__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
