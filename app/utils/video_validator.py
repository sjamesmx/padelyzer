from fastapi import HTTPException
import requests
import cv2
import os
from typing import Optional, Tuple
import logging
from urllib.parse import urlparse
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

# Constantes de validación
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_VIDEO_DURATION = 300  # 5 minutos
MIN_FPS = 24
SUPPORTED_FORMATS = ['.mp4', '.avi', '.mov', '.mkv']
MAX_RETRIES = 3
RETRY_DELAY = 2  # segundos

class VideoValidationError(Exception):
    """Excepción personalizada para errores de validación de video."""
    pass

async def validate_video_url(video_url: str) -> Tuple[bool, Optional[str]]:
    """
    Valida la URL del video y obtiene información básica.
    
    Args:
        video_url: URL del video a validar
        
    Returns:
        Tuple[bool, Optional[str]]: (es_válido, mensaje_error)
    """
    try:
        # Validar formato de URL
        parsed_url = urlparse(video_url)
        if not parsed_url.scheme in ['http', 'https', 'gs']:
            return False, "URL de video inválida"

        # Verificar tamaño del archivo
        async with aiohttp.ClientSession() as session:
            async with session.head(video_url) as response:
                if response.status != 200:
                    return False, f"Error al acceder al video: {response.status}"
                
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > MAX_VIDEO_SIZE:
                    return False, f"Video demasiado grande (máximo {MAX_VIDEO_SIZE/1024/1024}MB)"

        return True, None

    except Exception as e:
        logger.error(f"Error validando URL de video: {str(e)}")
        return False, f"Error validando video: {str(e)}"

async def validate_video_content(video_url: str) -> Tuple[bool, Optional[str]]:
    """
    Valida el contenido del video (duración, FPS, formato).
    
    Args:
        video_url: URL del video a validar
        
    Returns:
        Tuple[bool, Optional[str]]: (es_válido, mensaje_error)
    """
    try:
        # Descargar video temporalmente
        temp_path = f"/tmp/temp_video_{os.urandom(8).hex()}.mp4"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as response:
                if response.status != 200:
                    return False, "Error descargando video"
                
                with open(temp_path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)

        # Validar video con OpenCV
        cap = cv2.VideoCapture(temp_path)
        if not cap.isOpened():
            os.remove(temp_path)
            return False, "Video corrupto o no soportado"

        # Verificar FPS
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps < MIN_FPS:
            cap.release()
            os.remove(temp_path)
            return False, f"FPS demasiado bajo (mínimo {MIN_FPS})"

        # Verificar duración
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        if duration > MAX_VIDEO_DURATION:
            cap.release()
            os.remove(temp_path)
            return False, f"Video demasiado largo (máximo {MAX_VIDEO_DURATION} segundos)"

        cap.release()
        os.remove(temp_path)
        return True, None

    except Exception as e:
        logger.error(f"Error validando contenido de video: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False, f"Error validando video: {str(e)}"

async def validate_video_with_retry(video_url: str) -> None:
    """
    Valida el video con reintentos automáticos.
    
    Args:
        video_url: URL del video a validar
        
    Raises:
        HTTPException: Si la validación falla después de los reintentos
    """
    for attempt in range(MAX_RETRIES):
        try:
            # Validar URL
            is_valid, error_msg = await validate_video_url(video_url)
            if not is_valid:
                raise VideoValidationError(error_msg)

            # Validar contenido
            is_valid, error_msg = await validate_video_content(video_url)
            if not is_valid:
                raise VideoValidationError(error_msg)

            return

        except VideoValidationError as e:
            if attempt == MAX_RETRIES - 1:
                raise HTTPException(
                    status_code=400,
                    detail=str(e)
                )
            logger.warning(f"Intento {attempt + 1} fallido: {str(e)}")
            await asyncio.sleep(RETRY_DELAY)

        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error validando video: {str(e)}"
                )
            logger.warning(f"Intento {attempt + 1} fallido: {str(e)}")
            await asyncio.sleep(RETRY_DELAY) 