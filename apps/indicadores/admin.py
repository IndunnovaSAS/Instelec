"""
Admin configuration for indicators.
"""
from django.contrib import admin
from apps.core.admin import BaseModelAdmin
from .models import Indicador, MedicionIndicador, ActaSeguimiento


@admin.register(Indicador)
class IndicadorAdmin(BaseModelAdmin):
    list_display = ('codigo', 'nombre', 'categoria', 'meta', 'umbral_alerta', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('codigo', 'nombre')


@admin.register(MedicionIndicador)
class MedicionIndicadorAdmin(BaseModelAdmin):
    list_display = (
        'indicador', 'linea', 'mes', 'anio',
        'valor_calculado', 'cumple_meta', 'en_alerta'
    )
    list_filter = ('indicador', 'anio', 'mes', 'cumple_meta', 'en_alerta')
    raw_id_fields = ('indicador', 'linea')


@admin.register(ActaSeguimiento)
class ActaSeguimientoAdmin(BaseModelAdmin):
    list_display = ('linea', 'mes', 'anio', 'fecha_reunion', 'estado')
    list_filter = ('estado', 'anio', 'mes')
    raw_id_fields = ('linea',)
