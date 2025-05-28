from typing import Optional, Tuple
import logging
from firebase_admin import storage
from app.services.firebase import get_firebase_client
import os
from datetime import datetime
import mimetypes

logger = logging.getLogger(__name__)

class StorageService:
    # Formatos de video permitidos
    ALLOWED_VIDEO_FORMATS = ['video/mp4', 'video/quicktime']
    # Tamaño máximo de archivo (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024

    @staticmethod
    async def upload_video(file_data: bytes, filename: str, user_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Sube un video a Firebase Storage.
        
        Args:
            file_data: Contenido del archivo en bytes
            filename: Nombre original del archivo
            user_id: ID del usuario que sube el video
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (URL del video, mensaje de error)
        """
        try:
            # Obtener el bucket de Storage
            bucket = storage.bucket()
            
            # Validar el tamaño del archivo
            if len(file_data) > StorageService.MAX_FILE_SIZE:
                return None, "El archivo excede el tamaño máximo permitido (100MB)"
            
            # Validar la extensión del archivo
            file_extension = os.path.splitext(filename)[1].lower()
            if file_extension not in ['.mp4', '.mov']:
                return None, "Formato de archivo no permitido. Solo se permiten archivos MP4 y MOV"
            
            # Generar un nombre único para el archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"videos/{user_id}/{timestamp}_{filename}"
            
            # Crear una referencia al archivo en Storage
            blob = bucket.blob(safe_filename)
            
            # Determinar el tipo MIME
            content_type = mimetypes.guess_type(filename)[0] or 'video/mp4'
            
            # Subir el archivo
            blob.upload_from_string(
                file_data,
                content_type=content_type
            )
            
            # Generar URL pública
            blob.make_public()
            url = blob.public_url
            
            return url, None
            
        except Exception as e:
            logger.error(f"Error al subir video: {str(e)}")
            return None, str(e)

    @staticmethod
    async def delete_video(video_url: str) -> Tuple[bool, Optional[str]]:
        """
        Elimina un video de Firebase Storage.
        
        Args:
            video_url: URL del video a eliminar
            
        Returns:
            Tuple[bool, Optional[str]]: (éxito, mensaje de error)
        """
        try:
            # Obtener el bucket de Storage
            bucket = storage.bucket()
            
            # Extraer el nombre del archivo de la URL
            blob = bucket.blob(video_url.split('/')[-1])
            
            # Eliminar el archivo
            blob.delete()
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error al eliminar video: {str(e)}")
            return False, str(e)

    @staticmethod
    async def get_video_metadata(video_url: str) -> Tuple[Optional[dict], Optional[str]]:
        """
        Obtiene los metadatos de un video en Storage.
        
        Args:
            video_url: URL del video
            
        Returns:
            Tuple[Optional[dict], Optional[str]]: (metadatos, mensaje de error)
        """
        try:
            # Obtener el bucket de Storage
            bucket = storage.bucket()
            
            # Obtener los metadatos del archivo
            blob = bucket.blob(video_url.split('/')[-1])
            
            metadata = {
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'time_created': blob.time_created,
                'updated': blob.updated
            }
            
            return metadata, None
            
        except Exception as e:
            logger.error(f"Error al obtener metadatos del video: {str(e)}")
            return None, str(e)

def upload_file(file_path: str, destination_path: str) -> str:
    """
    Sube un archivo a Firebase Storage y retorna la URL pública.
    """
    try:
        db, _ = get_firebase_client()
        bucket = storage.bucket()
        blob = bucket.blob(destination_path)
        
        # Subir archivo
        blob.upload_from_filename(file_path)
        
        # Hacer el blob público
        blob.make_public()
        
        # Retornar URL pública
        return blob.public_url
    except Exception as e:
        logger.error(f"Error al subir archivo a Firebase Storage: {str(e)}")
        raise

def delete_file(file_path: str):
    """
    Elimina un archivo de Firebase Storage.
    """
    try:
        db, _ = get_firebase_client()
        bucket = storage.bucket()
        blob = bucket.blob(file_path)
        blob.delete()
    except Exception as e:
        logger.error(f"Error al eliminar archivo de Firebase Storage: {str(e)}")
        raise 