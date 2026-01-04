"""Celery tasks for KPI calculation and monitoring."""

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
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

    except Exception as exc:
        logger.error(f"Error calculating KPIs: {exc}")
        raise self.retry(exc=exc, countdown=60 * 5)  # Retry in 5 minutes


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

    except Exception as exc:
        logger.error(f"Error calculating global index: {exc}")
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
