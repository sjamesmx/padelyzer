import logging
from typing import Tuple, Optional
import asyncio
from fastapi import HTTPException, status
import aiohttp
import magic
import tempfile
import os

logger = logging.getLogger(__name__)

async def validate_video_with_retry(
    video_url: str,
    max_retries: int = 3,
    retry_delay: int = 2
) -> Tuple[bool, Optional[str]]:
    """
    Valida un video con reintentos en caso de fallo.
    
    Args:
        video_url: URL del video a validar
        max_retries: Número máximo de reintentos
        retry_delay: Tiempo de espera entre reintentos en segundos
        
    Returns:
        Tuple[bool, Optional[str]]: (éxito, mensaje de error si hay fallo)
    """
    for attempt in range(max_retries):
        try:
            success, error = await validate_video(video_url)
            if success:
                return True, None
            if attempt < max_retries - 1:
                logger.warning(f"Intento {attempt + 1} fallido: {error}. Reintentando en {retry_delay} segundos...")
                await asyncio.sleep(retry_delay)
            else:
                return False, error
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Error en intento {attempt + 1}: {str(e)}. Reintentando en {retry_delay} segundos...")
                await asyncio.sleep(retry_delay)
            else:
                return False, f"Error validando video después de {max_retries} intentos: {str(e)}"
    
    return False, "Número máximo de reintentos alcanzado"

async def validate_video(video_url: str) -> Tuple[bool, Optional[str]]:
    """
    Valida un video descargándolo y verificando su formato y contenido.
    
    Args:
        video_url: URL del video a validar
        
    Returns:
        Tuple[bool, Optional[str]]: (éxito, mensaje de error si hay fallo)
    """
    try:
        # Crear un archivo temporal
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            
        # Descargar el video
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as response:
                if response.status != 200:
                    return False, f"Error descargando video: HTTP {response.status}"
                
                # Guardar el contenido
                with open(temp_path, 'wb') as f:
                    while chunk := await response.content.read(8192):
                        f.write(chunk)
        
        # Verificar el tipo MIME
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(temp_path)
        
        if not file_type.startswith('video/'):
            return False, f"Archivo no es un video válido: {file_type}"
        
        # Verificar tamaño (máximo 100MB)
        file_size = os.path.getsize(temp_path)
        if file_size > 100 * 1024 * 1024:  # 100MB
            return False, "El video excede el tamaño máximo permitido (100MB)"
        
        # Limpiar
        os.unlink(temp_path)
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error validando video: {str(e)}")
        return False, f"Error validando video: {str(e)}"
    finally:
        # Asegurar limpieza del archivo temporal
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Error limpiando archivo temporal: {str(e)}") 