from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header, BackgroundTasks
from app.services.auth_service import verify_firebase_token
from app.services.storage_service import StorageService
from app.services.firebase import get_firebase_client
from typing import Optional
import logging
import uuid
import os
from google.cloud import tasks_v2
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/videos", tags=["videos"])

# Configuración de Cloud Tasks
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("CLOUD_TASKS_LOCATION", "us-central1")
QUEUE_NAME = os.getenv("CLOUD_TASKS_QUEUE", "padelyzer-analysis-queue")
CLOUD_RUN_URL = os.getenv("CLOUD_RUN_URL")  # Debe ser la URL base de tu servicio desplegado

def save_metrics_to_db(data: dict):
    """Guarda el estado inicial del análisis en Firestore (síncrono)."""
    db = get_firebase_client()
    db.collection('video_analyses').document(data['analysis_id']).set(data)

def enqueue_analysis_task(analysis_id: str):
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(PROJECT_ID, LOCATION, QUEUE_NAME)
    url = f"{CLOUD_RUN_URL}/tasks/analyze_video"
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"analysis_id": analysis_id}).encode(),
        }
    }
    client.create_task(parent=parent, task=task)

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    authorization: str = Header(...),
    background_tasks: BackgroundTasks = None
):
    """
    Sube un video, dispara el pipeline de análisis en background y almacena solo las métricas.
    Devuelve un ID de análisis para seguimiento.
    """
    try:
        # Verificar el token
        token = verify_firebase_token(authorization.replace("Bearer ", ""))
        user_id = token['uid']

        # Verificar el tipo de archivo
        if file.content_type not in StorageService.ALLOWED_VIDEO_FORMATS:
            logger.error(f"Formato de archivo no permitido: {file.content_type}")
            raise HTTPException(
                status_code=400,
                detail=f"Formato de archivo no permitido. Formatos permitidos: {StorageService.ALLOWED_VIDEO_FORMATS}"
            )

        # Leer el contenido del archivo
        file_data = await file.read()

        # Subir el video (temporalmente, si es necesario para el pipeline)
        video_url, error = await StorageService.upload_video(
            file_data=file_data,
            filename=file.filename,
            user_id=user_id
        )

        if error:
            logger.error(f"Error al subir video (detalle): {error}")
            raise HTTPException(status_code=400, detail=f"Error al subir video: {error}")

        # Generar un ID único de análisis
        analysis_id = str(uuid.uuid4())

        # Guardar estado inicial del análisis en la base de datos
        save_metrics_to_db({
            'analysis_id': analysis_id,
            'user_id': user_id,
            'status': 'pending',
            'video_url': video_url,
            'metrics': None
        })

        # Lanzar tarea de análisis asíncrono usando Cloud Tasks
        enqueue_analysis_task(analysis_id)

        # Responder con el ID de análisis para seguimiento
        return {"analysis_id": analysis_id, "status": "pending"}

    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado al subir video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@router.delete("/{video_url:path}")
async def delete_video(
    video_url: str,
    authorization: str = Header(...)
):
    """
    Elimina un video de Firebase Storage.
    
    Args:
        video_url: URL del video a eliminar
        authorization: Token de autenticación en el encabezado
        
    Returns:
        dict: Mensaje de éxito
    """
    try:
        # Verificar el token
        token = verify_firebase_token(authorization.replace("Bearer ", ""))
        
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
    authorization: str = Header(...)
):
    """
    Obtiene los metadatos de un video.
    
    Args:
        video_url: URL del video
        authorization: Token de autenticación en el encabezado
        
    Returns:
        dict: Metadatos del video
    """
    try:
        # Verificar el token
        token = verify_firebase_token(authorization.replace("Bearer ", ""))
        
        metadata, error = await StorageService.get_video_metadata(video_url)
        
        if error:
            raise HTTPException(status_code=400, detail=error)
            
        return metadata
        
    except Exception as e:
        logger.error(f"Error al obtener metadatos del video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 