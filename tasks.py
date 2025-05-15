from celery import Celery
from services.analysis_manager import AnalysisManager
from firebase_admin import firestore
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar Celery
celery_app = Celery('padelyzer')
celery_app.config_from_object('celeryconfig')

# Inicializar Firebase
db = firestore.client()
analysis_manager = AnalysisManager()

@celery_app.task(bind=True, max_retries=3)
def analyze_training_video(self, user_id: str, video_url: str, player_position: dict = None):
    """Analiza un video de entrenamiento."""
    try:
        # Actualizar estado en Firestore
        analysis_id = f"analysis_{self.request.id}"
        db.collection('video_analyses').document(analysis_id).set({
            'status': 'processing',
            'user_id': user_id,
            'video_url': video_url,
            'type': 'training'
        })

        # Procesar video
        result = analysis_manager.analyze_training_video(video_url, player_position)

        # Guardar resultados
        db.collection('video_analyses').document(analysis_id).update({
            'status': 'completed',
            'result': result,
            'completed_at': firestore.SERVER_TIMESTAMP
        })

        # Actualizar historial de Padel IQ
        db.collection('padel_iq_history').add({
            'user_id': user_id,
            'padel_iq': result['padel_iq'],
            'metrics': result['metrics'],
            'type': 'training',
            'created_at': firestore.SERVER_TIMESTAMP
        })

        return result

    except Exception as e:
        logger.error(f"Error en análisis de entrenamiento: {str(e)}")
        db.collection('video_analyses').document(analysis_id).update({
            'status': 'failed',
            'error': str(e),
            'failed_at': firestore.SERVER_TIMESTAMP
        })
        raise self.retry(exc=e)

@celery_app.task(bind=True, max_retries=3)
def analyze_game_video(self, user_id: str, video_url: str, player_position: dict = None):
    """Analiza un video de juego."""
    try:
        # Actualizar estado en Firestore
        analysis_id = f"analysis_{self.request.id}"
        db.collection('video_analyses').document(analysis_id).set({
            'status': 'processing',
            'user_id': user_id,
            'video_url': video_url,
            'type': 'game'
        })

        # Procesar video
        result = analysis_manager.analyze_game_video(video_url, player_position)

        # Guardar resultados
        db.collection('video_analyses').document(analysis_id).update({
            'status': 'completed',
            'result': result,
            'completed_at': firestore.SERVER_TIMESTAMP
        })

        # Actualizar historial de Padel IQ
        db.collection('padel_iq_history').add({
            'user_id': user_id,
            'padel_iq': result['padel_iq'],
            'metrics': result['metrics'],
            'type': 'game',
            'created_at': firestore.SERVER_TIMESTAMP
        })

        return result

    except Exception as e:
        logger.error(f"Error en análisis de juego: {str(e)}")
        db.collection('video_analyses').document(analysis_id).update({
            'status': 'failed',
            'error': str(e),
            'failed_at': firestore.SERVER_TIMESTAMP
        })
        raise self.retry(exc=e) 