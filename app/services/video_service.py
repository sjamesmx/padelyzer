import os
import uuid
from datetime import datetime
from firebase_admin import storage
from google.cloud import storage as google_storage
from app.core.config.firebase import initialize_firebase
from app.core.config import settings
import logging
from typing import List, Dict, Optional
import mimetypes

logger = logging.getLogger(__name__)

def get_storage_client():
    """Obtiene el cliente de Firebase Storage."""
    try:
        return storage.bucket()
    except Exception as e:
        logger.error(f"Error al obtener cliente de Storage: {str(e)}")
        raise

def validate_video_file(file_path: str) -> None:
    """
    Valida un archivo de video antes de subirlo.
    Raises:
        ValueError: Si el archivo no es válido
    """
    try:
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            raise ValueError("El archivo no existe")
            
        # Verificar el tamaño del archivo
        file_size = os.path.getsize(file_path)
        if file_size > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
            raise ValueError(f"El archivo excede el tamaño máximo permitido de {settings.MAX_VIDEO_SIZE_MB}MB")
            
        # Verificar el tipo de archivo
        mime_type = mimetypes.guess_type(file_path)[0]
        if not mime_type or not mime_type.startswith('video/'):
            raise ValueError("El archivo debe ser un video")
            
        # Verificar que el tipo de video está permitido
        if mime_type not in settings.ALLOWED_VIDEO_TYPES:
            raise ValueError(f"Tipo de video no permitido. Tipos permitidos: {', '.join(settings.ALLOWED_VIDEO_TYPES)}")
            
    except Exception as e:
        logger.error(f"Error al validar archivo de video: {str(e)}")
        raise ValueError(f"Error al validar archivo de video: {str(e)}")

def generate_video_path(user_id: str, filename: str) -> str:
    """
    Genera una ruta única para el video en Firebase Storage.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
    return f"videos/{user_id}/{timestamp}_{safe_filename}"

def upload_video(file_path: str, user_id: str, original_filename: str) -> Dict[str, str]:
    """
    Sube un vídeo a Firebase Storage.
    Returns:
        Dict[str, str]: Diccionario con la URL pública y la ruta de almacenamiento
    """
    try:
        # Validar archivo
        validate_video_file(file_path)
        
        bucket = get_storage_client()
        storage_path = generate_video_path(user_id, original_filename)
        
        blob = bucket.blob(storage_path)
        
        # Configurar metadatos
        blob.metadata = {
            'uploaded_by': user_id,
            'original_filename': original_filename,
            'upload_date': datetime.now().isoformat(),
            'content_type': mimetypes.guess_type(file_path)[0]
        }
        
        # Subir archivo
        blob.upload_from_filename(file_path)
        
        # Configurar el blob como público
        blob.make_public()
        
        # Generar URL usando la base de Firebase Storage
        base_url = f"https://firebasestorage.googleapis.com/v0/b/{settings.FIREBASE_STORAGE_BUCKET}/o"
        encoded_path = storage_path.replace('/', '%2F')
        video_url = f"{base_url}/{encoded_path}?alt=media"
        
        return {
            'url': video_url,
            'storage_path': storage_path
        }
    except Exception as e:
        logger.error(f"Error al subir vídeo: {str(e)}")
        raise

def delete_video(storage_path: str) -> bool:
    """
    Elimina un vídeo de Firebase Storage.
    Returns:
        bool: True si se eliminó correctamente
    """
    try:
        bucket = get_storage_client()
        blob = bucket.blob(storage_path)
        
        if not blob.exists():
            logger.warning(f"El archivo {storage_path} no existe")
            return False
            
        blob.delete()
        return True
    except Exception as e:
        logger.error(f"Error al eliminar vídeo: {str(e)}")
        return False

def get_video_metadata(storage_path: str) -> Optional[Dict]:
    """
    Obtiene los metadatos de un vídeo.
    Returns:
        Optional[Dict]: Metadatos del vídeo o None si no existe
    """
    try:
        bucket = get_storage_client()
        blob = bucket.blob(storage_path)
        
        if not blob.exists():
            return None
            
        return {
            'name': blob.name,
            'size': blob.size,
            'content_type': blob.content_type,
            'metadata': blob.metadata,
            'public_url': blob.public_url,
            'created': blob.time_created,
            'updated': blob.updated
        }
    except Exception as e:
        logger.error(f"Error al obtener metadatos del vídeo: {str(e)}")
        return None

def list_user_videos(user_id: str) -> List[Dict]:
    """
    Lista todos los vídeos de un usuario.
    Returns:
        List[Dict]: Lista de metadatos de los vídeos
    """
    try:
        bucket = get_storage_client()
        prefix = f"videos/{user_id}/"
        
        blobs = bucket.list_blobs(prefix=prefix)
        videos = []
        
        for blob in blobs:
            videos.append({
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'metadata': blob.metadata,
                'public_url': blob.public_url,
                'created': blob.time_created,
                'updated': blob.updated
            })
            
        return videos
    except Exception as e:
        logger.error(f"Error al listar vídeos del usuario: {str(e)}")
        return []

def get_video_blueprint(video_url: str) -> str:
    """
    Genera un blueprint único para un vídeo basado en su URL.
    Esto evita que el mismo vídeo se suba múltiples veces.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, video_url))

def analyze_video(video_path: str, user_id: str) -> dict:
    """
    Analiza un video y guarda los resultados en Firestore.
    """
    try:
        db, _ = get_firebase_client()
        
        # Crear documento de análisis
        analysis_ref = db.collection('video_analyses').document()
        analysis_data = {
            'video_path': video_path,
            'user_id': user_id,
            'status': 'processing',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        analysis_ref.set(analysis_data)
        
        # TODO: Implementar análisis de video
        # Por ahora, simulamos un análisis exitoso
        analysis_data.update({
            'status': 'completed',
            'results': {
                'duration': 120,
                'resolution': '1920x1080',
                'format': 'mp4'
            }
        })
        analysis_ref.update(analysis_data)
        
        return analysis_data
    except Exception as e:
        logger.error(f"Error al analizar video: {str(e)}")
        raise

def get_video_analysis(analysis_id: str) -> Optional[dict]:
    """
    Obtiene los resultados de un análisis de video.
    """
    try:
        db, _ = get_firebase_client()
        analysis_ref = db.collection('video_analyses').document(analysis_id)
        analysis_doc = analysis_ref.get()
        
        if not analysis_doc.exists:
            return None
            
        analysis_data = analysis_doc.to_dict()
        analysis_data['id'] = analysis_doc.id
        return analysis_data
    except Exception as e:
        logger.error(f"Error al obtener análisis de video: {str(e)}")
        return None 