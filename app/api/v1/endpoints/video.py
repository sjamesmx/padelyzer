from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.schemas.video import (
    VideoCreate, VideoResponse, VideoType, VideoStatus,
    VideoAnalysisRequest, VideoAnalysisResponse
)
from app.services.firebase import get_firebase_client
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
from datetime import datetime
import logging
from typing import List

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/training", response_model=VideoResponse, summary="Subir video de entrenamiento", tags=["videos"])
async def upload_training_video(
    video: VideoCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Sube un video de entrenamiento.
    """
    try:
        if video.type != VideoType.TRAINING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El tipo debe ser 'training' para este endpoint"
            )

        db = get_firebase_client()
        video_data = video.dict()
        video_data.update({
            "user_id": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": VideoStatus.PENDING
        })

        video_ref = db.collection("videos").document()
        video_data["id"] = video_ref.id
        video_ref.set(video_data)

        logger.info(f"Video de entrenamiento subido por {current_user.id}: {video_data['id']}")
        return video_data

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error al subir video de entrenamiento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al subir video de entrenamiento"
        )

@router.post("/game", response_model=VideoResponse, summary="Subir video de juego", tags=["videos"])
async def upload_game_video(
    video: VideoCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Sube un video de juego.
    """
    try:
        if video.type != VideoType.GAME:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El tipo debe ser 'game' para este endpoint"
            )

        db = get_firebase_client()
        video_data = video.dict()
        video_data.update({
            "user_id": current_user.id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": VideoStatus.PENDING
        })

        video_ref = db.collection("videos").document()
        video_data["id"] = video_ref.id
        video_ref.set(video_data)

        logger.info(f"Video de juego subido por {current_user.id}: {video_data['id']}")
        return video_data

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error al subir video de juego: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al subir video de juego"
        )

@router.get("/", response_model=List[VideoResponse], summary="Obtener lista de videos", tags=["videos"])
async def get_videos(current_user: UserInDB = Depends(get_current_user)):
    """
    Obtiene la lista de videos del usuario.
    """
    try:
        db = get_firebase_client()
        videos_ref = db.collection("videos").where("user_id", "==", current_user.id).get()
        videos = [video.to_dict() for video in videos_ref]

        logger.info(f"Videos obtenidos para {current_user.id}: {len(videos)} videos")
        return videos

    except Exception as e:
        logger.error(f"Error al obtener videos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener videos"
        )

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

@router.post("/analyze", response_model=VideoAnalysisResponse, summary="Analizar video", tags=["videos"])
async def analyze_video(
    request: VideoAnalysisRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Inicia el análisis de un video.
    """
    try:
        db = get_firebase_client()
        video_ref = db.collection("videos").document(request.video_id).get()

        if not video_ref.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video no encontrado"
            )

        video_data = video_ref.to_dict()
        if video_data["user_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autorizado para analizar este video"
            )

        # Actualizar estado a "processing"
        video_ref.reference.update({
            "status": VideoStatus.PROCESSING,
            "updated_at": datetime.utcnow()
        })

        # TODO: Implementar análisis real con MediaPipe
        # Por ahora, simulamos un análisis
        analysis_result = {
            "movements_detected": 10,
            "accuracy": 0.85,
            "analysis_type": request.analysis_type
        }

        # Actualizar video con resultado del análisis
        video_ref.reference.update({
            "status": VideoStatus.COMPLETED,
            "analysis_result": analysis_result,
            "updated_at": datetime.utcnow()
        })

        logger.info(f"Análisis completado para video {request.video_id} por {current_user.id}")
        return VideoAnalysisResponse(
            video_id=request.video_id,
            status=VideoStatus.COMPLETED,
            analysis_result=analysis_result
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error al analizar video {request.video_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al analizar video"
        )

@router.delete("/{video_id}")
async def delete_video_endpoint(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint para eliminar un video.
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
                detail="No tienes permiso para eliminar este video"
            )
            
        # Eliminar video de Firebase Storage
        delete_file(video_data['video_path'])
        
        # Eliminar documento de video
        video_ref.delete()
        
        return {"message": "Video eliminado correctamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar video: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar el video"
        ) 