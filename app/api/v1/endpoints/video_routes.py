from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Form
from app.api.v1.schemas.video_schema import VideoUploadRequest, VideoUploadResponse, VideoStatus
from app.services.video_service import get_video_blueprint
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
from app.services.firebase import get_firebase_client
from app.worker import analyze_video
from app.tasks.video import process_video
from datetime import datetime
import logging
import tempfile
import os
from typing import Optional

router = APIRouter(prefix="/video", tags=["video"])
logger = logging.getLogger(__name__)

@router.delete("/{video_url:path}")
async def delete_video(
    video_url: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Elimina un video de Firebase Storage.
    
    Args:
        video_url: URL del video a eliminar
        current_user: Usuario actual
        
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
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtiene los metadatos de un video.
    
    Args:
        video_url: URL del video
        current_user: Usuario actual
        
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

@router.get("/analysis/{video_id}", response_model=VideoUploadResponse)
async def get_video_analysis(
    video_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtiene el estado y resultados del análisis de un video.
    """
    try:
        db, _ = get_firebase_client()
        analysis_ref = db.collection('video_analyses').document(video_id)
        analysis_doc = analysis_ref.get()
        
        if not analysis_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Análisis no encontrado"
            )
            
        analysis_data = analysis_doc.to_dict()
        
        # Verificar que el usuario tenga acceso al análisis
        if analysis_data['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver este análisis"
            )
            
        return VideoUploadResponse(
            video_id=video_id,
            url=analysis_data['video_url'],
            status=VideoStatus(analysis_data['status']),
            created_at=analysis_data['created_at'],
            message="Análisis encontrado",
            padel_iq=analysis_data.get('padel_iq'),
            metrics=analysis_data.get('metrics')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo análisis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo análisis: {str(e)}"
        ) 