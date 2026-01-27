"""
Admin configuration for transmission lines.
"""
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from apps.core.admin import BaseModelAdmin
from .models import Linea, Torre, PoligonoServidumbre, Tramo


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


@admin.register(Tramo)
class TramoAdmin(BaseModelAdmin):
    list_display = ('codigo', 'nombre', 'linea', 'torre_inicio', 'torre_fin', 'numero_vanos', 'total_torres')
    list_filter = ('linea',)
    search_fields = ('codigo', 'nombre', 'linea__codigo')
    raw_id_fields = ('linea', 'torre_inicio', 'torre_fin')

    fieldsets = (
        (None, {
            'fields': ('codigo', 'nombre', 'linea')
        }),
        ('Rango de Torres', {
            'fields': ('torre_inicio', 'torre_fin')
        }),
        ('Información calculada', {
            'fields': ('numero_vanos_display', 'total_torres_display'),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('id', 'created_at', 'updated_at', 'numero_vanos_display', 'total_torres_display')

    def numero_vanos_display(self, obj):
        return obj.numero_vanos
    numero_vanos_display.short_description = 'Número de vanos'

    def total_torres_display(self, obj):
        return obj.total_torres
    total_torres_display.short_description = 'Total de torres'
