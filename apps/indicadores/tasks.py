"""Celery tasks for KPI calculation and monitoring."""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db import DatabaseError
from datetime import date

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def calcular_indicadores_mensuales(self, linea_id=None, anio=None, mes=None):
    """
    Calculate monthly KPIs for all lines or a specific line.
    Runs automatically on the 5th of each month for the previous month.
    """
    from apps.lineas.models import Linea
    from .calculators import calcular_todos_indicadores

    # Default to previous month
    if anio is None or mes is None:
        hoy = date.today()
        if hoy.month == 1:
            anio = hoy.year - 1
            mes = 12
        else:
            anio = hoy.year
            mes = hoy.month - 1

    try:
        if linea_id:
            lineas = Linea.objects.filter(id=linea_id, activa=True)
        else:
            lineas = Linea.objects.filter(activa=True)

        resultados = []
        for linea in lineas:
            logger.info(f"Calculating KPIs for line {linea.codigo} - {anio}/{mes}")
            resultado = calcular_todos_indicadores(linea.id, anio, mes)
            resultados.append({
                'linea': linea.codigo,
                'indicadores': resultado
            })

        logger.info(f"Calculated KPIs for {len(resultados)} lines")
        return resultados

    except DatabaseError as exc:
        logger.error(f"Database error calculating KPIs: {exc}")
        raise self.retry(exc=exc, countdown=60 * 5)  # Retry in 5 minutes
    except (ValueError, TypeError, ZeroDivisionError) as exc:
        logger.error(f"Calculation error in KPIs: {exc}")
        raise self.retry(exc=exc, countdown=60 * 5)


@shared_task(bind=True)
def calcular_indice_global_todas_lineas(self, anio=None, mes=None):
    """Calculate global performance index for all lines."""
    from apps.lineas.models import Linea
    from .calculators import calcular_indice_global

    if anio is None or mes is None:
        hoy = date.today()
        anio = hoy.year
        mes = hoy.month

    try:
        lineas = Linea.objects.filter(activa=True)
        resultados = []

        for linea in lineas:
            indice, detalles = calcular_indice_global(linea.id, anio, mes)
            resultados.append({
                'linea': linea.codigo,
                'indice_global': float(indice),
                'detalles': detalles
            })

        return resultados

    except DatabaseError as exc:
        logger.error(f"Database error calculating global index: {exc}")
        raise
    except (ValueError, TypeError, ZeroDivisionError) as exc:
        logger.error(f"Calculation error in global index: {exc}")
        raise


@shared_task
def verificar_alertas_indicadores():
    """
    Check for KPI alerts and send notifications.
    Runs daily to detect indicators below threshold.
    """
    from django.core.mail import send_mail
    from django.conf import settings
    from .models import MedicionIndicador
    from apps.usuarios.models import Usuario

    hoy = date.today()

    # Get measurements with alerts from current month
    mediciones_alerta = MedicionIndicador.objects.filter(
        anio=hoy.year,
        mes=hoy.month,
        en_alerta=True
    ).select_related('indicador', 'linea')

    if not mediciones_alerta.exists():
        logger.info("No KPI alerts found")
        return []

    # Group by line
    alertas_por_linea = {}
    for medicion in mediciones_alerta:
        linea_codigo = medicion.linea.codigo
        if linea_codigo not in alertas_por_linea:
            alertas_por_linea[linea_codigo] = []
        alertas_por_linea[linea_codigo].append({
            'indicador': medicion.indicador.nombre,
            'valor': float(medicion.valor_calculado),
            'meta': float(medicion.indicador.meta),
            'umbral': float(medicion.indicador.umbral_alerta)
        })

    # Notify supervisors
    supervisores = Usuario.objects.filter(
        rol__in=['SUPERVISOR', 'ADMINISTRADOR'],
        is_active=True
    ).values_list('email', flat=True)

    for linea_codigo, alertas in alertas_por_linea.items():
        mensaje = f"Alertas de indicadores para línea {linea_codigo}:\n\n"
        for alerta in alertas:
            mensaje += f"- {alerta['indicador']}: {alerta['valor']:.1f}% "
            mensaje += f"(Meta: {alerta['meta']:.1f}%, Umbral: {alerta['umbral']:.1f}%)\n"

        logger.warning(f"KPI alerts for line {linea_codigo}: {len(alertas)} alerts")

    return alertas_por_linea


@shared_task
def generar_resumen_semanal():
    """Generate weekly KPI summary report."""
    from apps.lineas.models import Linea
    from .models import MedicionIndicador
    from datetime import timedelta

    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())

    lineas = Linea.objects.filter(activa=True)
    resumen = []

    for linea in lineas:
        mediciones = MedicionIndicador.objects.filter(
            linea=linea,
            anio=hoy.year,
            mes=hoy.month
        ).select_related('indicador')

        indicadores = {}
        for med in mediciones:
            indicadores[med.indicador.codigo] = {
                'valor': float(med.valor_calculado),
                'cumple': med.cumple_meta,
                'alerta': med.en_alerta
            }

        resumen.append({
            'linea': linea.codigo,
            'indicadores': indicadores,
            'cumple_todos': all(i['cumple'] for i in indicadores.values()),
            'alertas': sum(1 for i in indicadores.values() if i['alerta'])
        })

    logger.info(f"Weekly summary generated for {len(resumen)} lines")
    return resumen


@shared_task
def verificar_rendimiento(actividad_id: str):
    """
    Verifica el rendimiento de una actividad comparando avance real vs esperado.
    Genera alertas cuando el avance es inferior al rendimiento estándar.
    """
    from apps.actividades.models import Actividad
    from decimal import Decimal

    try:
        actividad = Actividad.objects.select_related(
            'tipo_actividad', 'cuadrilla', 'linea', 'tramo'
        ).get(id=actividad_id)
    except Actividad.DoesNotExist:
        logger.error(f"Activity not found: {actividad_id}")
        return {'error': 'Activity not found', 'actividad_id': actividad_id}

    # Calcular días transcurridos desde inicio
    hoy = date.today()
    if actividad.fecha_programada > hoy:
        return {
            'actividad_id': actividad_id,
            'status': 'no_iniciada',
            'message': 'Actividad aún no programada para iniciar'
        }

    dias_transcurridos = (hoy - actividad.fecha_programada).days + 1

    # Rendimiento esperado según tipo de actividad
    rendimiento_diario = actividad.tipo_actividad.rendimiento_estandar_vanos

    # Si hay tramo, calcular vanos totales
    vanos_totales = 0
    if actividad.tramo:
        vanos_totales = actividad.tramo.numero_vanos

    # Calcular avance esperado
    if vanos_totales > 0:
        # Avance esperado = (rendimiento_diario * días) / vanos_totales * 100
        vanos_esperados = rendimiento_diario * dias_transcurridos
        avance_esperado = min(Decimal('100'), (Decimal(str(vanos_esperados)) / Decimal(str(vanos_totales))) * 100)
    else:
        # Si no hay tramo, usar un avance estimado basado en tiempo
        avance_esperado = min(Decimal('100'), Decimal(str(dias_transcurridos * 10)))  # 10% por día como estimado

    avance_real = actividad.porcentaje_avance
    diferencia = avance_real - avance_esperado

    # Determinar estado de rendimiento
    if diferencia >= 0:
        estado = 'normal'
        nivel_alerta = None
    elif diferencia >= -10:
        estado = 'bajo'
        nivel_alerta = 'warning'
    else:
        estado = 'critico'
        nivel_alerta = 'critical'

    resultado = {
        'actividad_id': actividad_id,
        'linea': actividad.linea.codigo,
        'cuadrilla': actividad.cuadrilla.codigo if actividad.cuadrilla else None,
        'tipo_actividad': actividad.tipo_actividad.nombre,
        'dias_transcurridos': dias_transcurridos,
        'rendimiento_diario_esperado': rendimiento_diario,
        'vanos_totales': vanos_totales,
        'avance_esperado': float(avance_esperado),
        'avance_real': float(avance_real),
        'diferencia': float(diferencia),
        'estado': estado,
        'nivel_alerta': nivel_alerta
    }

    if nivel_alerta:
        logger.warning(
            f"Low performance alert for activity {actividad_id}: "
            f"Real={avance_real}%, Expected={avance_esperado}%, "
            f"Diff={diferencia}%, State={estado}"
        )

    return resultado


@shared_task
def generar_alertas_rendimiento():
    """
    Genera alertas de rendimiento para todas las actividades en curso.
    Se ejecuta diariamente para detectar actividades con bajo rendimiento.
    """
    from apps.actividades.models import Actividad
    from django.core.mail import send_mail
    from apps.usuarios.models import Usuario

    hoy = date.today()

    # Obtener actividades en curso
    actividades = Actividad.objects.filter(
        estado__in=['EN_CURSO', 'PROGRAMADA'],
        fecha_programada__lte=hoy
    ).select_related('tipo_actividad', 'cuadrilla', 'linea', 'tramo')

    alertas = []

    for actividad in actividades:
        resultado = verificar_rendimiento.apply(args=[str(actividad.id)])
        if resultado.get('nivel_alerta'):
            alertas.append(resultado)

    # Agrupar alertas por nivel
    alertas_criticas = [a for a in alertas if a.get('nivel_alerta') == 'critical']
    alertas_warning = [a for a in alertas if a.get('nivel_alerta') == 'warning']

    logger.info(
        f"Performance alerts generated: "
        f"{len(alertas_criticas)} critical, {len(alertas_warning)} warnings"
    )

    return {
        'total_actividades': len(actividades),
        'total_alertas': len(alertas),
        'alertas_criticas': len(alertas_criticas),
        'alertas_warning': len(alertas_warning),
        'detalle': alertas
    }


@shared_task
def generar_reporte_rendimiento_cuadrillas(fecha_inicio: str = None, fecha_fin: str = None):
    """
    Genera un reporte de rendimiento por cuadrilla.
    Compara el rendimiento real vs esperado de cada cuadrilla.
    """
    from apps.actividades.models import Actividad
    from apps.cuadrillas.models import Cuadrilla
    from datetime import datetime
    from decimal import Decimal

    hoy = date.today()

    if fecha_inicio:
        inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    else:
        inicio = hoy.replace(day=1)  # Primer día del mes actual

    if fecha_fin:
        fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    else:
        fin = hoy

    cuadrillas = Cuadrilla.objects.filter(activa=True)
    reporte = []

    for cuadrilla in cuadrillas:
        actividades = Actividad.objects.filter(
            cuadrilla=cuadrilla,
            fecha_programada__gte=inicio,
            fecha_programada__lte=fin
        ).select_related('tipo_actividad', 'tramo')

        if not actividades.exists():
            continue

        total_avance_real = Decimal('0')
        total_avance_esperado = Decimal('0')
        actividades_count = 0

        for actividad in actividades:
            resultado = verificar_rendimiento.apply(args=[str(actividad.id)])
            if 'error' not in resultado:
                total_avance_real += Decimal(str(resultado['avance_real']))
                total_avance_esperado += Decimal(str(resultado['avance_esperado']))
                actividades_count += 1

        if actividades_count > 0:
            promedio_real = total_avance_real / actividades_count
            promedio_esperado = total_avance_esperado / actividades_count
            eficiencia = (promedio_real / promedio_esperado * 100) if promedio_esperado > 0 else Decimal('100')

            reporte.append({
                'cuadrilla': cuadrilla.codigo,
                'nombre': cuadrilla.nombre,
                'supervisor': cuadrilla.supervisor.get_full_name() if cuadrilla.supervisor else None,
                'total_actividades': actividades_count,
                'avance_promedio_real': float(promedio_real),
                'avance_promedio_esperado': float(promedio_esperado),
                'eficiencia': float(eficiencia),
                'estado': 'excelente' if eficiencia >= 100 else 'normal' if eficiencia >= 80 else 'bajo'
            })

    # Ordenar por eficiencia descendente
    reporte.sort(key=lambda x: x['eficiencia'], reverse=True)

    logger.info(f"Crew performance report generated: {len(reporte)} crews analyzed")

    return {
        'periodo': f"{inicio} - {fin}",
        'total_cuadrillas': len(reporte),
        'cuadrillas': reporte
    }
