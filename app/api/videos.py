from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.services.auth_service import verify_firebase_token
from app.services.storage_service import StorageService
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/videos", tags=["videos"])

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    token: str = Depends(verify_firebase_token)
):
    """
    Sube un video a Firebase Storage.
    
    Args:
        file: Archivo de video a subir
        token: Token de autenticación
        
    Returns:
        dict: URL del video subido
    """
    try:
        # Verificar el tipo de archivo
        if file.content_type not in StorageService.ALLOWED_VIDEO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Formato de archivo no permitido. Formatos permitidos: {StorageService.ALLOWED_VIDEO_FORMATS}"
            )
        
        # Leer el contenido del archivo
        file_data = await file.read()
        
        # Subir el video
        video_url, error = await StorageService.upload_video(
            file_data=file_data,
            filename=file.filename,
            user_id=token['uid']
        )
        
        if error:
            raise HTTPException(status_code=400, detail=error)
            
        return {"url": video_url}
        
    except Exception as e:
        logger.error(f"Error al subir video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{video_url:path}")
async def delete_video(
    video_url: str,
    token: str = Depends(verify_firebase_token)
):
    """
    Elimina un video de Firebase Storage.
    
    Args:
        video_url: URL del video a eliminar
        token: Token de autenticación
        
    Returns:
        dict: Mensaje de éxito
    """
    try:
        success, error = await StorageService.delete_video(video_url)
        
        if not success:
            raise HTTPException(status_code=400, detail=error)
            
        return {"message": "Video eliminado correctamente"}
        
    except Exception as e:
        logger.error(f"Error al eliminar video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{video_url:path}/metadata")
async def get_video_metadata(
    video_url: str,
    token: str = Depends(verify_firebase_token)
):
    """
    Obtiene los metadatos de un video.
    
    Args:
        video_url: URL del video
        token: Token de autenticación
        
    Returns:
        dict: Metadatos del video
    """
    try:
        metadata, error = await StorageService.get_video_metadata(video_url)
        
        if error:
            raise HTTPException(status_code=400, detail=error)
            
        return metadata
        
    except Exception as e:
        logger.error(f"Error al obtener metadatos del video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 