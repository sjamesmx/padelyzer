import logging
from celery import Celery
from app.core.config import settings
from app.services.analysis_manager import AnalysisManager
from app.services.notifications import notification_service
from app.services.firebase import get_firebase_client
from datetime import datetime
from typing import Dict, Any, Optional

# Configurar logging
logger = logging.getLogger(__name__)

# Inicializar Celery
celery_app = Celery(
    'padelyzer',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configurar Celery
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
    task_acks_late=settings.CELERY_TASK_ACKS_LATE,
    task_reject_on_worker_lost=settings.CELERY_TASK_REJECT_ON_WORKER_LOST,
    task_default_queue=settings.CELERY_TASK_DEFAULT_QUEUE,
    task_queues=settings.CELERY_TASK_QUEUES,
    task_routes=settings.CELERY_TASK_ROUTES
)

def create_analysis_document(db, user_id: str, video_url: str, tipo_video: str, 
                           estado: str, analysis_result: Optional[Dict[str, Any]] = None,
                           error: Optional[str] = None) -> str:
    """
    Crea un documento de análisis en Firestore.
    
    Args:
        db: Cliente de Firestore
        user_id: ID del usuario
        video_url: URL del video
        tipo_video: Tipo de video
        estado: Estado del análisis
        analysis_result: Resultados del análisis (opcional)
        error: Mensaje de error (opcional)
        
    Returns:
        str: ID del documento creado
    """
    analysis_ref = db.collection('video_analisis').document()
    analysis_data = {
        'user_id': user_id,
        'video_url': video_url,
        'tipo_video': tipo_video,
        'estado': estado,
        'created_at': datetime.utcnow()
    }
    
    if estado == 'completed' and analysis_result:
        analysis_data.update({
            'padel_iq': analysis_result.get('padel_iq'),
            'analysis_result': analysis_result,
            'completed_at': datetime.utcnow()
        })
    elif estado == 'failed' and error:
        analysis_data.update({
            'error': error,
            'failed_at': datetime.utcnow()
        })
    
    analysis_ref.set(analysis_data)
    return analysis_ref.id

@celery_app.task(name="app.tasks.analyze_video", bind=True, max_retries=settings.VIDEO_ANALYSIS_RETRY_COUNT)
def analyze_video(self, user_id: str, video_url: str, tipo_video: str, player_position: dict) -> Dict[str, Any]:
    """
    Tarea asíncrona para analizar un video.
    
    Args:
        user_id: ID del usuario que subió el video
        video_url: URL del video en Firebase Storage
        tipo_video: Tipo de video ('entrenamiento' o 'juego')
        player_position: Posición del jugador en el video
        
    Returns:
        Dict[str, Any]: Resultados del análisis
    """
    try:
        logger.info(f"Iniciando análisis asíncrono para user_id: {user_id}, video_url: {video_url}")
        
        # Obtener cliente de Firestore
        db = get_firebase_client()
        
        # Crear instancia del gestor de análisis
        analysis_manager = AnalysisManager()
        
        # Realizar análisis según el tipo de video
        if tipo_video == "entrenamiento":
            analysis_result = analysis_manager.analyze_training_video(
                video_url=video_url,
                player_position=player_position
            )
        else:  # tipo_video == "juego"
            analysis_result = analysis_manager.analyze_game_video(
                video_url=video_url,
                player_position=player_position
            )
        
        # Crear documento de análisis
        analysis_id = create_analysis_document(
            db=db,
            user_id=user_id,
            video_url=video_url,
            tipo_video=tipo_video,
            estado='completed',
            analysis_result=analysis_result
        )
        
        # Crear notificación de éxito
        notification_service.create_notification(
            user_id=user_id,
            type='video_analysis_complete',
            title=settings.NOTIFICATION_TYPES['video_analysis_complete']['title'],
            message=settings.NOTIFICATION_TYPES['video_analysis_complete']['message'],
            data={
                'analysis_id': analysis_id,
                'padel_iq': analysis_result.get('padel_iq'),
                'video_url': video_url
            }
        )
        
        logger.info(f"Análisis completado para user_id: {user_id}, video_url: {video_url}")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error en análisis de video: {str(e)}", exc_info=True)
        
        try:
            # Crear documento de análisis con error
            analysis_id = create_analysis_document(
                db=db,
                user_id=user_id,
                video_url=video_url,
                tipo_video=tipo_video,
                estado='failed',
                error=str(e)
            )
            
            # Crear notificación de error
            notification_service.create_notification(
                user_id=user_id,
                type='video_analysis_failed',
                title=settings.NOTIFICATION_TYPES['video_analysis_failed']['title'],
                message=settings.NOTIFICATION_TYPES['video_analysis_failed']['message'],
                data={
                    'analysis_id': analysis_id,
                    'error': str(e),
                    'video_url': video_url
                }
            )
        except Exception as notify_error:
            logger.error(f"Error al crear notificación de error: {str(notify_error)}")
        
        # Reintentar la tarea si es posible
        try:
            self.retry(exc=e, countdown=settings.VIDEO_ANALYSIS_RETRY_DELAY)
        except self.MaxRetriesExceededError:
            logger.error("Se excedió el número máximo de reintentos")
            raise
        
        # Si llegamos aquí, significa que no se pudo reintentar la tarea
        return {
            'error': str(e),
            'status': 'failed',
            'message': settings.ERROR_MESSAGES['video_analysis_failed']
        } 