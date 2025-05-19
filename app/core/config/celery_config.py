from app.core.config import settings
from celery import Celery
from typing import Dict, Any

def create_celery_app() -> Celery:
    """
    Crea y configura una instancia de Celery.
    
    Returns:
        Celery: Instancia configurada de Celery
    """
    celery_app = Celery(
        'padelyzer',
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND
    )
    
    # Configuración de Celery
    celery_app.conf.update(
        task_serializer=settings.CELERY_TASK_SERIALIZER,
        accept_content=settings.CELERY_ACCEPT_CONTENT,
        result_serializer=settings.CELERY_RESULT_SERIALIZER,
        timezone=settings.CELERY_TIMEZONE,
        enable_utc=settings.CELERY_ENABLE_UTC,
        task_track_started=settings.CELERY_TASK_TRACK_STARTED,
        task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
        task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
        worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
        worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
        
        # Configuraciones adicionales
        task_acks_late=True,  # Las tareas se confirman después de completarse
        task_reject_on_worker_lost=True,  # Rechazar tareas si el worker se pierde
        task_default_queue='default',  # Cola por defecto
        task_queues={
            'default': {
                'exchange': 'default',
                'routing_key': 'default',
            },
            'video_analysis': {
                'exchange': 'video_analysis',
                'routing_key': 'video_analysis',
            }
        },
        task_routes={
            'app.tasks.analyze_video': {
                'queue': 'video_analysis',
                'routing_key': 'video_analysis',
            }
        }
    )
    
    return celery_app

# Crear instancia de Celery
celery_app = create_celery_app() 