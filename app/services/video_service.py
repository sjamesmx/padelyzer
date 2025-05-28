import os
import uuid
from datetime import datetime
from firebase_admin import storage
from google.cloud import storage as google_storage
from app.core.config.firebase import initialize_firebase, get_firebase_clients
from app.core.config import settings
import logging
from typing import List, Dict, Optional, Tuple
import mimetypes
import magic
from fastapi import HTTPException, APIRouter, Depends, UploadFile, File
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

class VideoValidationError(Exception):
    """Excepción personalizada para errores de validación de vídeo."""
    pass

def get_storage_client():
    """Obtiene el cliente de Firebase Storage."""
    try:
        return storage.bucket()
    except Exception as e:
        logger.error(f"Error al obtener cliente de Storage: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al conectar con el servicio de almacenamiento"
        )

def validate_video_file(file_path: str) -> Tuple[bool, str]:
    """
    Valida un archivo de video antes de subirlo.
    Returns:
        Tuple[bool, str]: (es_válido, mensaje_error)
    """
    try:
        logger.info(f"Validando archivo de video: {file_path}")
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            return False, "El archivo no existe"
            
        # Verificar el tamaño del archivo
        file_size = os.path.getsize(file_path)
        logger.info(f"Tamaño del archivo: {file_size} bytes")
        if file_size > settings.MAX_VIDEO_SIZE_MB * 1024 * 1024:
            return False, f"El archivo excede el tamaño máximo permitido de {settings.MAX_VIDEO_SIZE_MB}MB"
            
        # Verificar la extensión del archivo
        file_extension = os.path.splitext(file_path)[1].lower()
        logger.info(f"Extensión del archivo: {file_extension}")
        allowed_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.wmv']
        if file_extension not in allowed_extensions:
            return False, f"Extensión de archivo no permitida. Extensiones permitidas: {', '.join(allowed_extensions)}"
            
        # Verificar el tipo MIME
        try:
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(file_path)
        except ImportError:
            mime_type = mimetypes.guess_type(file_path)[0]
            
        logger.info(f"Tipo MIME detectado: {mime_type}")
        
        if not mime_type:
            logger.warning("No se pudo detectar el tipo MIME, verificando por extensión")
            return True, ""
            
        if not mime_type.startswith('video/'):
            return False, "El archivo debe ser un video"
            
        # Verificar que el tipo de video está permitido
        if mime_type not in settings.ALLOWED_VIDEO_TYPES and mime_type != 'video/quicktime':
            return False, f"Tipo de video no permitido. Tipos permitidos: {', '.join(settings.ALLOWED_VIDEO_TYPES)}"
            
        logger.info("Validación de archivo de video completada exitosamente")
        return True, ""
            
    except Exception as e:
        logger.error(f"Error al validar archivo de video: {str(e)}")
        return False, f"Error al validar archivo de video: {str(e)}"

def generate_video_path(user_id: str, filename: str) -> str:
    """
    Genera una ruta única para el video en Firebase Storage.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
    unique_id = str(uuid.uuid4())[:8]
    return f"videos/{user_id}/{timestamp}_{unique_id}_{safe_filename}"

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

def get_video_blueprint() -> APIRouter:
    """Obtiene el router para las rutas de video."""
    router = APIRouter()
    
    @router.post("/upload")
    async def upload_video(
        file: UploadFile = File(...),
        current_user = Depends(get_current_user)
    ):
        """Sube un video a Firebase Storage."""
        try:
            # Obtener clientes de Firebase
            clients = get_firebase_clients()
            storage = clients['storage']
            
            # Crear nombre único para el archivo
            file_name = f"videos/{current_user['uid']}/{file.filename}"
            
            # Subir archivo
            blob = storage.blob(file_name)
            blob.upload_from_file(file.file)
            
            return {"message": "Video subido correctamente", "file_name": file_name}
        except Exception as e:
            logger.error(f"Error al subir video: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/list")
    async def list_videos(
        current_user = Depends(get_current_user)
    ):
        """Lista los videos del usuario."""
        try:
            # Obtener clientes de Firebase
            clients = get_firebase_clients()
            storage = clients['storage']
            
            # Listar archivos
            prefix = f"videos/{current_user['uid']}/"
            blobs = storage.list_blobs(prefix=prefix)
            
            videos = []
            for blob in blobs:
                videos.append({
                    "name": blob.name,
                    "url": blob.public_url,
                    "size": blob.size,
                    "updated": blob.updated
                })
            
            return videos
        except Exception as e:
            logger.error(f"Error al listar videos: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return router

def get_video_analysis(analysis_id: str) -> Optional[dict]:
    """
    Obtiene los resultados de un análisis de video.
    """
    try:
        db, _ = get_firebase_clients()
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