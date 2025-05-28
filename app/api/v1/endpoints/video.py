from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.schemas.video import VideoResponse
from app.services.firebase import get_firebase_client
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{video_id}", response_model=VideoResponse, summary="Obtener video específico", tags=["videos"])
async def get_video(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para obtener información de un video.
    """
    try:
        db, _ = get_firebase_client()
        video_ref = db.collection('videos').document(video_id)
        video_doc = video_ref.get()
        
        if not video_doc.exists:
            raise HTTPException(
                status_code=404,
                detail="Video no encontrado"
            )
            
        video_data = video_doc.to_dict()
        
        # Verificar que el usuario tenga acceso al video
        if video_data['user_id'] != current_user['id']:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para ver este video"
            )
            
        return VideoResponse(
            video_id=video_doc.id,
            video_url=video_data['video_url'],
            status=video_data['status'],
            created_at=video_data['created_at'],
            updated_at=video_data['updated_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener video: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al obtener el video"
        ) 