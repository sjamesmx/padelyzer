import os
import uuid
from datetime import datetime
from firebase_admin import storage
from google.cloud import storage as google_storage
from app.config.firebase import initialize_firebase
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

def validate_video_file(file_path: str) -> bool:
    """
    Valida que el archivo sea un vídeo y cumpla con los requisitos.
    Returns:
        bool: True si el archivo es válido
    """
    try:
        # Verificar tamaño
        file_size = os.path.getsize(file_path)
        if file_size > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
            raise ValueError(f"El archivo excede el tamaño máximo permitido de {settings.MAX_VIDEO_SIZE_MB}MB")

        # Verificar tipo de archivo
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type or not mime_type.startswith('video/'):
            raise ValueError("El archivo debe ser un vídeo")

        if mime_type not in settings.ALLOWED_VIDEO_TYPES:
            raise ValueError(f"Tipo de vídeo no permitido. Tipos permitidos: {settings.ALLOWED_VIDEO_TYPES}")

        return True
    except Exception as e:
        logger.error(f"Error al validar archivo: {str(e)}")
        raise

def generate_video_path(user_id: str, original_filename: str) -> str:
    """Genera una ruta única para el vídeo."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())
    extension = os.path.splitext(original_filename)[1]
    return f"videos/{user_id}/{timestamp}_{unique_id}{extension}"

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
        
        return {
            'url': blob.public_url,
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