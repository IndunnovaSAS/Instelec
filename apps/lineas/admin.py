"""
Admin configuration for transmission lines.
"""
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from apps.core.admin import BaseModelAdmin
from .models import Linea, Torre, PoligonoServidumbre


class TorreInline(admin.TabularInline):
    model = Torre
    extra = 0
    fields = ('numero', 'tipo', 'estado', 'latitud', 'longitud', 'municipio')
    readonly_fields = ('id',)
    show_change_link = True


@admin.register(Linea)
class LineaAdmin(BaseModelAdmin):
    list_display = ('codigo', 'nombre', 'cliente', 'tension_kv', 'longitud_km', 'total_torres', 'activa')
    list_filter = ('cliente', 'activa', 'departamento')
    search_fields = ('codigo', 'nombre', 'municipios')
    inlines = [TorreInline]

    fieldsets = (
        (None, {
            'fields': ('codigo', 'nombre', 'cliente')
        }),
        ('Características', {
            'fields': ('tension_kv', 'longitud_km', 'departamento', 'municipios')
        }),
        ('Estado', {
            'fields': ('activa', 'observaciones')
        }),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Torre)
class TorreAdmin(GISModelAdmin):
    list_display = ('numero', 'linea', 'tipo', 'estado', 'municipio', 'latitud', 'longitud')
    list_filter = ('linea', 'tipo', 'estado', 'municipio')
    search_fields = ('numero', 'linea__codigo', 'propietario_predio', 'vereda')
    raw_id_fields = ('linea',)

    fieldsets = (
        (None, {
            'fields': ('linea', 'numero', 'tipo', 'estado')
        }),
        ('Ubicación', {
            'fields': ('latitud', 'longitud', 'altitud', 'geometria')
        }),
        ('Información del predio', {
            'fields': ('propietario_predio', 'vereda', 'municipio')
        }),
        ('Detalles', {
            'fields': ('altura_estructura', 'observaciones')
        }),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(PoligonoServidumbre)
class PoligonoServidumbreAdmin(GISModelAdmin):
    list_display = ('__str__', 'linea', 'torre', 'area_hectareas', 'ancho_franja')
    list_filter = ('linea',)
    search_fields = ('nombre', 'torre__numero', 'linea__codigo')
    raw_id_fields = ('linea', 'torre')

    fieldsets = (
        (None, {
            'fields': ('nombre', 'linea', 'torre')
        }),
        ('Geometría', {
            'fields': ('geometria', 'area_hectareas', 'ancho_franja')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
    )
    readonly_fields = ('id', 'created_at', 'updated_at', 'area_hectareas')
