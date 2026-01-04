"""
KPI calculation functions for transmission line maintenance contracts.

Indicators calculated:
- Gestión de Mantenimiento (Maintenance Management)
- Ejecución de Mantenimiento (Maintenance Execution)
- Gestión Ambiental (Environmental Management)
- Calidad de Información (Information Quality)
- Seguridad Industrial (Industrial Safety)
- Cumplimiento de Cronograma (Schedule Compliance)
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Tuple

from django.db.models import Count, Q, Avg
from django.utils import timezone


def calcular_gestion_mantenimiento(linea_id, anio, mes):
    """
    Calculate maintenance management indicator.
    Formula: (Executed activities / Planned activities) * 100
    """
    from apps.actividades.models import Actividad

    actividades = Actividad.objects.filter(
        linea_id=linea_id,
        fecha_programada__year=anio,
        fecha_programada__month=mes
    )

    total_programadas = actividades.count()
    ejecutadas = actividades.filter(estado='COMPLETADA').count()

    if total_programadas == 0:
        return Decimal('0'), Decimal('0'), Decimal('0')

    valor = (Decimal(ejecutadas) / Decimal(total_programadas)) * 100

    return Decimal(ejecutadas), Decimal(total_programadas), valor


def calcular_ejecucion_mantenimiento(linea_id, anio, mes):
    """
    Calculate maintenance execution indicator.
    Formula: (Activities completed on time / Total completed) * 100
    """
    from apps.actividades.models import Actividad

    completadas = Actividad.objects.filter(
        linea_id=linea_id,
        fecha_programada__year=anio,
        fecha_programada__month=mes,
        estado='COMPLETADA'
    )

    total_completadas = completadas.count()

    # Activities completed on the scheduled date
    # (comparing with field record date)
    a_tiempo = 0
    for act in completadas:
        registro = act.registros_campo.first()
        if registro and registro.fecha_fin:
            if registro.fecha_fin.date() <= act.fecha_programada:
                a_tiempo += 1

    if total_completadas == 0:
        return Decimal('0'), Decimal('0'), Decimal('0')

    valor = (Decimal(a_tiempo) / Decimal(total_completadas)) * 100

    return Decimal(a_tiempo), Decimal(total_completadas), valor


def calcular_gestion_ambiental(linea_id, anio, mes):
    """
    Calculate environmental management indicator.
    Formula: (Reports delivered on time / Required reports) * 100
    """
    from apps.ambiental.models import InformeAmbiental

    # Check if monthly report was delivered on time
    try:
        informe = InformeAmbiental.objects.get(
            linea_id=linea_id,
            periodo_anio=anio,
            periodo_mes=mes
        )

        # Assume due date is 10th of following month
        from datetime import date
        if mes == 12:
            fecha_limite = date(anio + 1, 1, 10)
        else:
            fecha_limite = date(anio, mes + 1, 10)

        a_tiempo = 1 if informe.fecha_envio and informe.fecha_envio.date() <= fecha_limite else 0
        total = 1
        valor = Decimal('100') if a_tiempo else Decimal('0')

    except InformeAmbiental.DoesNotExist:
        a_tiempo = 0
        total = 1
        valor = Decimal('0')

    return Decimal(a_tiempo), Decimal(total), valor


def calcular_calidad_informacion(linea_id, anio, mes):
    """
    Calculate information quality indicator.
    Formula: (Complete records / Total records) * 100
    """
    from apps.campo.models import RegistroCampo

    registros = RegistroCampo.objects.filter(
        actividad__linea_id=linea_id,
        fecha_inicio__year=anio,
        fecha_inicio__month=mes,
        sincronizado=True
    )

    total = registros.count()
    completos = 0

    for reg in registros:
        if reg.evidencias_completas and reg.datos_formulario:
            completos += 1

    if total == 0:
        return Decimal('0'), Decimal('0'), Decimal('0')

    valor = (Decimal(completos) / Decimal(total)) * 100

    return Decimal(completos), Decimal(total), valor


def calcular_seguridad_industrial(linea_id, anio, mes):
    """
    Calculate industrial safety indicator.
    Formula: (Days without accidents / Working days in month) * 100
    """
    from apps.actividades.models import Actividad
    from apps.campo.models import RegistroCampo
    import calendar

    # Get working days in month (weekdays)
    cal = calendar.Calendar()
    dias_laborables = sum(
        1 for d in cal.itermonthdays2(anio, mes)
        if d[0] != 0 and d[1] < 5  # weekdays only
    )

    # Count days with registered activities
    registros = RegistroCampo.objects.filter(
        actividad__linea_id=linea_id,
        fecha_inicio__year=anio,
        fecha_inicio__month=mes
    )

    # Check for accidents in form data
    dias_con_accidentes = 0
    for reg in registros:
        if reg.datos_formulario.get('accidente_reportado', False):
            dias_con_accidentes += 1

    dias_sin_accidentes = dias_laborables - dias_con_accidentes

    if dias_laborables == 0:
        return Decimal('0'), Decimal('0'), Decimal('0')

    valor = (Decimal(dias_sin_accidentes) / Decimal(dias_laborables)) * 100

    return Decimal(dias_sin_accidentes), Decimal(dias_laborables), valor


def calcular_cumplimiento_cronograma(linea_id, anio, mes):
    """
    Calculate schedule compliance indicator.
    Formula: (Activities started on scheduled date / Total scheduled) * 100
    """
    from apps.actividades.models import Actividad
    from apps.campo.models import RegistroCampo

    actividades = Actividad.objects.filter(
        linea_id=linea_id,
        fecha_programada__year=anio,
        fecha_programada__month=mes
    ).exclude(estado='CANCELADA')

    total_programadas = actividades.count()
    iniciadas_a_tiempo = 0

    for act in actividades:
        registro = act.registros_campo.first()
        if registro and registro.fecha_inicio:
            if registro.fecha_inicio.date() <= act.fecha_programada:
                iniciadas_a_tiempo += 1

    if total_programadas == 0:
        return Decimal('0'), Decimal('0'), Decimal('0')

    valor = (Decimal(iniciadas_a_tiempo) / Decimal(total_programadas)) * 100

    return Decimal(iniciadas_a_tiempo), Decimal(total_programadas), valor


def calcular_indice_global(linea_id, anio, mes):
    """
    Calculate global performance index.
    Weighted average of all indicators.
    """
    pesos = {
        'GESTION': Decimal('0.20'),
        'EJECUCION': Decimal('0.25'),
        'AMBIENTAL': Decimal('0.15'),
        'CALIDAD': Decimal('0.15'),
        'SEGURIDAD': Decimal('0.15'),
        'CRONOGRAMA': Decimal('0.10'),
    }

    calculadores = {
        'GESTION': calcular_gestion_mantenimiento,
        'EJECUCION': calcular_ejecucion_mantenimiento,
        'AMBIENTAL': calcular_gestion_ambiental,
        'CALIDAD': calcular_calidad_informacion,
        'SEGURIDAD': calcular_seguridad_industrial,
        'CRONOGRAMA': calcular_cumplimiento_cronograma,
    }

    indice_global = Decimal('0')
    detalles = {}

    for categoria, calculador in calculadores.items():
        _, _, valor = calculador(linea_id, anio, mes)
        peso = pesos.get(categoria, Decimal('0'))
        contribucion = valor * peso
        indice_global += contribucion
        detalles[categoria] = {
            'valor': float(valor),
            'peso': float(peso),
            'contribucion': float(contribucion)
        }

    return indice_global, detalles


def calcular_todos_indicadores(linea_id, anio, mes):
    """Calculate and save all indicators for a period."""
    from .models import Indicador, MedicionIndicador

    calculadores = {
        'GESTION': calcular_gestion_mantenimiento,
        'EJECUCION': calcular_ejecucion_mantenimiento,
        'AMBIENTAL': calcular_gestion_ambiental,
        'CALIDAD': calcular_calidad_informacion,
        'SEGURIDAD': calcular_seguridad_industrial,
        'CRONOGRAMA': calcular_cumplimiento_cronograma,
    }

    resultados = []

    for indicador in Indicador.objects.filter(activo=True):
        calculador = calculadores.get(indicador.categoria)

        if calculador:
            numerador, denominador, valor = calculador(linea_id, anio, mes)

            medicion, created = MedicionIndicador.objects.update_or_create(
                indicador=indicador,
                linea_id=linea_id,
                anio=anio,
                mes=mes,
                defaults={
                    'valor_numerador': numerador,
                    'valor_denominador': denominador,
                    'valor_calculado': valor,
                    'cumple_meta': valor >= indicador.meta,
                    'en_alerta': valor < indicador.umbral_alerta,
                }
            )

            resultados.append({
                'indicador': indicador.codigo,
                'valor': float(valor),
                'cumple': medicion.cumple_meta,
            })

    return resultados
