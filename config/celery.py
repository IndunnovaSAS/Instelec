import os
from celery import Celery

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
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
