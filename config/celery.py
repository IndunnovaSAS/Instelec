import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

app = Celery('transmaint')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Task queues configuration
app.conf.task_queues = {
    'high_priority': {'exchange': 'high', 'routing_key': 'high'},
    'default': {'exchange': 'default', 'routing_key': 'default'},
    'reports': {'exchange': 'reports', 'routing_key': 'reports'},
}

app.conf.task_routes = {
    'apps.campo.tasks.*': {'queue': 'high_priority'},
    'apps.ambiental.tasks.*': {'queue': 'reports'},
    'apps.financiero.tasks.*': {'queue': 'reports'},
    'apps.indicadores.tasks.*': {'queue': 'default'},
}

# Celery Beat schedule - automated periodic tasks
app.conf.beat_schedule = {
    # KPI Calculations
    'calcular-indicadores-mensuales': {
        'task': 'apps.indicadores.tasks.calcular_indicadores_mensuales',
        'schedule': crontab(hour=6, minute=0, day_of_month=5),  # 5th of each month at 6 AM
        'description': 'Calculate monthly KPIs for all lines'
    },
    'verificar-alertas-indicadores': {
        'task': 'apps.indicadores.tasks.verificar_alertas_indicadores',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8 AM
        'description': 'Check for KPI alerts'
    },
    'resumen-semanal-indicadores': {
        'task': 'apps.indicadores.tasks.generar_resumen_semanal',
        'schedule': crontab(hour=7, minute=0, day_of_week=1),  # Mondays at 7 AM
        'description': 'Generate weekly KPI summary'
    },

    # Environmental Reports
    'verificar-permisos-vencidos': {
        'task': 'apps.ambiental.tasks.verificar_permisos_vencidos',
        'schedule': crontab(hour=7, minute=0),  # Daily at 7 AM
        'description': 'Check for expired easement permits'
    },
    'generar-informes-ambientales': {
        'task': 'apps.ambiental.tasks.generar_informes_periodo',
        'schedule': crontab(hour=2, minute=0, day_of_month=1),  # 1st of each month at 2 AM
        'args': (),  # Will use previous month automatically
        'description': 'Generate monthly environmental reports'
    },

    # Financial Reports
    'calcular-costos-actividades': {
        'task': 'apps.financiero.tasks.calcular_costos_actividades',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
        'description': 'Calculate costs for completed activities'
    },
    'generar-cuadro-costos': {
        'task': 'apps.financiero.tasks.generar_cuadro_costos_mensual',
        'schedule': crontab(hour=3, minute=0, day_of_month=1),  # 1st of each month at 3 AM
        'description': 'Generate monthly cost table'
    },
    'reporte-presupuestal-semanal': {
        'task': 'apps.financiero.tasks.generar_reporte_presupuestal',
        'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Mondays at 8 AM
        'description': 'Generate weekly budget report'
    },
    'consolidar-costos-mensuales': {
        'task': 'apps.financiero.tasks.consolidar_costos_mensuales',
        'schedule': crontab(hour=4, minute=0, day_of_month=2),  # 2nd of each month at 4 AM
        'description': 'Consolidate monthly costs by category'
    },
}

# Timezone for beat schedule
app.conf.timezone = 'America/Bogota'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
