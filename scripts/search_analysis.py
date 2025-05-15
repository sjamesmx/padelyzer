import os
import sys
import logging
from datetime import datetime
from google.cloud import firestore

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.firebase import get_firebase_client

def search_analysis(task_id: str, user_id: str):
    """
    Busca el análisis en las colecciones relevantes.
    """
    try:
        db = get_firebase_client()
        
        # Colecciones específicas de análisis
        collections = {
            'video_analisis': ['user_id', 'video_url', 'estado', 'fecha_analisis'],
            'player_strokes': ['user_id', 'timestamp', 'strokes'],
            'padel_iq_history': ['user_id', 'timestamp', 'padel_iq', 'tipo_analisis']
        }
        
        logger.info(f"Buscando análisis con task_id: {task_id}")
        logger.info(f"Usuario: {user_id}")
        
        for collection_name, fields in collections.items():
            logger.info(f"\nBuscando en colección: {collection_name}")
            collection_ref = db.collection(collection_name)
            
            # Buscar por user_id
            query = collection_ref.where('user_id', '==', user_id).limit(5)
            results = query.get()
            
            if results:
                logger.info(f"\nDocumentos recientes para el usuario en {collection_name}:")
                for doc in results:
                    logger.info(f"ID: {doc.id}")
                    data = doc.to_dict()
                    # Mostrar solo los campos relevantes
                    filtered_data = {k: v for k, v in data.items() if k in fields}
                    logger.info(f"Datos: {filtered_data}")
                    logger.info("---")
            
            # Buscar documentos creados en los últimos 5 minutos
            five_minutes_ago = datetime.now().timestamp() - 300
            query = collection_ref.where('timestamp', '>=', five_minutes_ago).limit(5)
            results = query.get()
            
            if results:
                logger.info(f"\nDocumentos recientes en {collection_name}:")
                for doc in results:
                    logger.info(f"ID: {doc.id}")
                    data = doc.to_dict()
                    # Mostrar solo los campos relevantes
                    filtered_data = {k: v for k, v in data.items() if k in fields}
                    logger.info(f"Datos: {filtered_data}")
                    logger.info("---")
    except Exception as e:
        logger.error(f"Error al buscar análisis: {str(e)}")
        raise

if __name__ == "__main__":
    task_id = "c2a791d1-822c-455b-9d75-3d2b85c83205"
    user_id = "nuevo_usuario_004@example.com"
    search_analysis(task_id, user_id) 