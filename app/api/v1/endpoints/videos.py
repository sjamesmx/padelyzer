from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from app.schemas.video import VideoUpload, VideoAnalysis, VideoAnalysisResponse, VideoStatus, VideoCreate, VideoResponse, VideoType, VideoAnalysisRequest
from app.services.storage import upload_video, delete_video, get_video_blueprint
from app.services.firebase import get_firebase_client
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
from app.tasks import celery_app
import tempfile
import os
import logging
from datetime import datetime
from typing import Optional, List
import json
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

analyze_video = celery_app.tasks['app.tasks.analyze_video']

@router.post("/upload", response_model=VideoAnalysisResponse)
async def upload_video_endpoint(
    file: UploadFile = File(...),
    tipo_video: str = Form(...),
    descripcion: Optional[str] = Form(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Sube un vídeo para análisis.
    - El vídeo se almacena temporalmente en Firebase Storage
    - Se genera un blueprint único para evitar duplicados
    - Se inicia el análisis del vídeo
    """
    try:
        # Validar tipo de archivo
        if not file.content_type or not file.content_type.startswith('video/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo debe ser un vídeo"
            )

        # Validar nombre de archivo
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo debe tener un nombre"
            )

        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Subir a Firebase Storage
            video_data = upload_video(temp_path, current_user.id, file.filename)
            video_url = video_data['url']
            
            # Generar blueprint
            blueprint = get_video_blueprint(video_url)
            
            # Verificar si ya existe un análisis con este blueprint
            db = get_firebase_client()
            existing_analysis = db.collection('video_analisis').where('blueprint', '==', blueprint).limit(1).get()
            
            if existing_analysis:
                # Si existe, devolver el análisis existente
                analysis_data = existing_analysis[0].to_dict()
                return VideoAnalysisResponse(
                    analysis_id=existing_analysis[0].id,
                    status=VideoStatus.COMPLETED,
                    message="Análisis ya existente"
                )
            
            # Crear documento de análisis
            analysis_ref = db.collection('video_analisis').document()
            analysis_data = {
                'user_id': current_user.id,
                'video_url': video_url,
                'tipo_video': tipo_video,
                'fecha_analisis': datetime.now(),
                'estado': VideoStatus.PENDING,
                'blueprint': blueprint,
                'descripcion': descripcion
            }
            analysis_ref.set(analysis_data)
            
            # Iniciar análisis asíncrono con todos los argumentos requeridos
            analyze_video.delay(
                user_id=current_user.id,
                video_url=video_url,
                tipo_video=tipo_video,
                player_position={"position": "derecha"}  # Valor por defecto
            )
            
            return VideoAnalysisResponse(
                analysis_id=analysis_ref.id,
                status=VideoStatus.PENDING,
                message="Vídeo subido y análisis iniciado"
            )
            
        finally:
            # Limpiar archivo temporal
            os.unlink(temp_path)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al subir vídeo: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el vídeo: {str(e)}"
        )

@router.get("/analysis/{analysis_id}", response_model=VideoAnalysis)
async def get_analysis_status(
    analysis_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtiene el estado de un análisis de vídeo.
    """
    try:
        db = get_firebase_client()
        analysis_doc = db.collection('video_analisis').document(analysis_id).get()
        
        if not analysis_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Análisis no encontrado"
            )
            
        analysis_data = analysis_doc.to_dict()
        
        # Verificar que el usuario tenga acceso
        if analysis_data['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver este análisis"
            )
            
        return VideoAnalysis(**analysis_data, id=analysis_doc.id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener estado del análisis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener estado del análisis"
        )

@router.post("/training", response_model=VideoResponse, summary="Subir video de entrenamiento", tags=["videos"])
async def upload_training_video(
    video: VideoCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    try:
        if video.type != VideoType.ENTRENAMIENTO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El tipo debe ser 'entrenamiento' para este endpoint"
            )
        db = get_firebase_client()
        video_data = video.dict()
        video_data["url"] = str(video_data["url"])
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
    try:
        if video.type != VideoType.JUEGO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El tipo debe ser 'juego' para este endpoint"
            )
        db = get_firebase_client()
        video_data = video.dict()
        video_data["url"] = str(video_data["url"])
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
async def get_videos_token(current_user: dict = Depends(get_current_user)):
    try:
        db = get_firebase_client()
        videos_ref = db.collection("videos").where("user_id", "==", current_user["sub"]).get()
        videos = [video.to_dict() for video in videos_ref]
        logger.info(f"Videos obtenidos para {current_user['sub']}: {len(videos)} videos")
        return videos
    except Exception as e:
        logger.error(f"Error al obtener videos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener videos"
        )

@router.get("/{video_id}", response_model=VideoResponse, summary="Obtener video específico", tags=["videos"])
async def get_video_token(
    video_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        db = get_firebase_client()
        video_ref = db.collection("videos").document(video_id).get()
        if not video_ref.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video no encontrado"
            )
        video_data = video_ref.to_dict()
        if video_data["user_id"] != current_user["sub"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autorizado para ver este video"
            )
        logger.info(f"Video obtenido para {current_user['sub']}: {video_id}")
        return video_data
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error al obtener video {video_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener video"
        )

@router.post("/analyze", response_model=VideoAnalysisResponse, summary="Analizar video", tags=["videos"])
async def analyze_video(
    request: VideoAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        db = get_firebase_client()
        # Buscar el análisis por blueprint o video_url
        # Aquí solo simulamos el análisis
        analysis_id = "simulated-analysis-id"
        return VideoAnalysisResponse(
            analysis_id=analysis_id,
            status=VideoStatus.PROCESSING,
            message="Análisis iniciado (simulado)"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error al analizar video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al analizar video"
        ) 