from celery import Celery
import os

# Configuración de Celery
celery_app = Celery(
    'padelyzer',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['app.tasks']
)

# Configuración adicional
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hora de límite por tarea
    task_soft_time_limit=3300,  # 55 minutos de límite suave
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50
) 