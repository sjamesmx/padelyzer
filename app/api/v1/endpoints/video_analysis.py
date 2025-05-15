from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Query
from app.core.config import settings
import logging
from fastapi import HTTPException as RealHTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from app.services.analysis_manager import AnalysisManager  # Ajusta la ruta si es necesario
from firebase_admin import firestore
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
import uuid
from app.tasks import analyze_video

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar AnalysisManager
analysis_manager = AnalysisManager()

# Definir el router de FastAPI
router = APIRouter()

# Modelos para validar las solicitudes
class PadelIQRequest(BaseModel):
    user_id: str
    video_url: HttpUrl
    tipo_video: str
    player_position: dict = {"side": "left", "zone": "back"}
    game_splits: dict = None

class VideoAnalyzeRequest(BaseModel):
    user_id: str
    video_url: HttpUrl
    tipo_video: str
    player_position: dict = {"side": "left", "zone": "back"}

# Modelo para la respuesta
class VideoAnalysisResponse(BaseModel):
    padel_iq: float
    metrics: dict
    error: Optional[str] = None

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

# Constantes para validación
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_VIDEO_DURATION = 3600  # 1 hora
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/quicktime", "video/x-msvideo"]

# Endpoint para subir videos
@router.post("/upload")
async def upload_video(file: UploadFile = File(...), current_user: UserInDB = Depends(get_current_user)):
    """Sube un video para análisis con validaciones."""
    # Validar tipo de archivo
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado. Tipos permitidos: {', '.join(ALLOWED_VIDEO_TYPES)}"
        )

    # Validar tamaño
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB
    while chunk := await file.read(chunk_size):
        file_size += len(chunk)
        if file_size > MAX_VIDEO_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"El archivo excede el tamaño máximo permitido de {MAX_VIDEO_SIZE/1024/1024}MB"
            )
    await file.seek(0)

    # Validar duración (simulado)
    # En producción, esto debería usar ffprobe o similar
    video_duration = 0  # Simulado
    if video_duration > MAX_VIDEO_DURATION:
        raise HTTPException(
            status_code=400,
            detail=f"El video excede la duración máxima permitida de {MAX_VIDEO_DURATION/60} minutos"
        )

    # Procesar subida
    db = get_db()
    video_id = str(uuid.uuid4())
    video_url = f"https://storage.padzr.com/videos/{video_id}.mp4"
    
    # Guardar metadata con estado inicial
    video_doc = {
        "user_id": current_user.id,
        "filename": file.filename,
        "content_type": file.content_type,
        "video_url": video_url,
        "size_bytes": file_size,
        "duration_seconds": video_duration,
        "status": "uploaded",
        "uploaded_at": firestore.SERVER_TIMESTAMP,
        "analysis_status": "pending"
    }
    
    db.collection("videos").document(video_id).set(video_doc)
    
    return {
        "video_id": video_id,
        "video_url": video_url,
        "status": "uploaded",
        "message": "Video subido correctamente. El análisis comenzará pronto."
    }

@router.get("/analysis/history")
async def get_analysis_history(current_user: UserInDB = Depends(get_current_user)):
    """Devuelve el histórico de análisis del usuario autenticado."""
    db = get_db()
    analyses = db.collection("video_analysis").where("user_id", "==", current_user.id).order_by("created_at", direction=firestore.Query.DESCENDING).get()
    return [a.to_dict() for a in analyses]

@router.get("/analysis/{video_id}")
async def get_analysis(video_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Devuelve el detalle de un análisis específico."""
    db = get_db()
    doc = db.collection("video_analysis").document(video_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    analysis = doc.to_dict()
    if analysis.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver este análisis")
    return analysis

@router.get("/analysis/compare")
async def compare_analyses(video_id_1: str, video_id_2: str, current_user: UserInDB = Depends(get_current_user)):
    """Compara métricas entre dos análisis de video."""
    db = get_db()
    doc1 = db.collection("video_analysis").document(video_id_1).get()
    doc2 = db.collection("video_analysis").document(video_id_2).get()
    if not doc1.exists or not doc2.exists:
        raise HTTPException(status_code=404, detail="Uno o ambos análisis no encontrados")
    a1, a2 = doc1.to_dict(), doc2.to_dict()
    if a1.get("user_id") != current_user.id or a2.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para comparar estos análisis")
    # Comparar métricas clave
    comparison = {k: {"video_1": a1["metrics"].get(k), "video_2": a2["metrics"].get(k)} for k in set(a1["metrics"]).union(a2["metrics"])}
    return {"video_1": video_id_1, "video_2": video_id_2, "comparison": comparison}

@router.get("/analysis/recommendations")
async def get_recommendations(video_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Ofrece recomendaciones personalizadas basadas en el análisis de un video."""
    db = get_db()
    doc = db.collection("video_analysis").document(video_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    analysis = doc.to_dict()
    if analysis.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver este análisis")
    metrics = analysis.get("metrics", {})
    recs = []
    if metrics.get("tecnica", 0) < 60:
        recs.append("Mejora tu técnica con ejercicios de control de pala.")
    if metrics.get("ritmo", 0) < 50:
        recs.append("Trabaja en tu ritmo de juego con sesiones de intervalos.")
    if metrics.get("fuerza", 0) < 50:
        recs.append("Aumenta tu fuerza con ejercicios de muñeca y antebrazo.")
    if metrics.get("court_coverage", 0) < 0.5:
        recs.append("Mejora tu cobertura de pista con drills de desplazamiento.")
    if not recs:
        recs.append("¡Excelente desempeño! Sigue así para mantener tu nivel.")
    return {"video_id": video_id, "recommendations": recs}

@router.post("/process_training_video")
async def process_training_video():
    raise HTTPException(status_code=501, detail="Not Implemented")

def determine_force_category(padel_iq: float, tecnica: float, ritmo: float, fuerza: float) -> str:
    """Determina la categoría de fuerza del jugador basada en sus métricas."""
    # Primera fuerza: Padel IQ > 85 y todas las métricas > 80
    if padel_iq > 85 and tecnica > 80 and ritmo > 80 and fuerza > 80:
        return "primera_fuerza"
    # Segunda fuerza: Padel IQ > 75 y todas las métricas > 70
    elif padel_iq > 75 and tecnica > 70 and ritmo > 70 and fuerza > 70:
        return "segunda_fuerza"
    # Tercera fuerza: Padel IQ > 65 y todas las métricas > 60
    elif padel_iq > 65 and tecnica > 60 and ritmo > 60 and fuerza > 60:
        return "tercera_fuerza"
    # Cuarta fuerza: Padel IQ > 45 y todas las métricas > 40
    elif padel_iq > 45 and tecnica > 40 and ritmo > 40 and fuerza > 40:
        return "cuarta_fuerza"
    # Quinta fuerza: resto de jugadores
    else:
        return "quinta_fuerza"

@router.get("/analysis/status/{video_id}")
async def get_analysis_status(video_id: str, current_user: UserInDB = Depends(get_current_user)):
    """Consulta el estado actual del análisis de un video."""
    db = get_db()
    doc = db.collection("videos").document(video_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    
    video_data = doc.to_dict()
    if video_data.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para ver este video")
    
    return {
        "video_id": video_id,
        "status": video_data.get("status", "unknown"),
        "analysis_status": video_data.get("analysis_status", "unknown"),
        "progress": video_data.get("analysis_progress", 0),
        "error": video_data.get("analysis_error"),
        "created_at": video_data.get("uploaded_at"),
        "completed_at": video_data.get("analysis_completed_at")
    }

@router.post("/calculate_padel_iq")
async def calculate_padel_iq(data: PadelIQRequest, current_user: UserInDB = Depends(get_current_user)):
    """Procesa un video y calcula métricas de Padel IQ. Guarda el análisis en Firestore."""
    # Extraer datos de la solicitud
    user_id = current_user.id
    video_url = data.video_url
    tipo_video = data.tipo_video
    player_position = data.player_position
    game_splits = data.game_splits

    # Validar datos requeridos
    if not user_id or not video_url or not tipo_video:
        logger.error("Faltan datos requeridos en la solicitud")
        raise HTTPException(status_code=400, detail="Faltan datos requeridos (user_id, video_url, tipo_video)")

    logger.info(f"Procesando video para user_id: {user_id}, video_url: {video_url}, tipo_video: {tipo_video}")

    try:
        # Actualizar estado del video
        db = get_db()
        video_id = str(uuid.uuid4())
        db.collection("videos").document(video_id).update({
            "analysis_status": "processing",
            "analysis_progress": 0,
            "analysis_started_at": firestore.SERVER_TIMESTAMP
        })

        # Procesar el video según el tipo
        if tipo_video == "entrenamiento":
            logger.info("Iniciando procesamiento de video de entrenamiento")
            result = analysis_manager.procesar_video_entrenamiento(
                video_url=video_url,
                user_id=user_id,
                player_position=player_position
            )
        elif tipo_video == "juego":
            logger.info("Iniciando procesamiento de video de juego")
            result = analysis_manager.procesar_video_juego(
                video_url=video_url,
                user_id=user_id,
                player_position=player_position,
                game_splits=game_splits
            )
        else:
            logger.error("Tipo de video no soportado")
            db.collection("videos").document(video_id).update({
                "analysis_status": "error",
                "analysis_error": "Tipo de video no soportado"
            })
            raise HTTPException(status_code=400, detail="Tipo de video no soportado")

        metrics = result.get("metrics", {})
        padel_iq = result.get("padel_iq", 0.0)
        player_level = "Principiante" if padel_iq < 30 else "Intermedio" if padel_iq < 60 else "Avanzado"
        force_category = determine_force_category(
            padel_iq,
            metrics.get("tecnica", 0),
            metrics.get("ritmo", 0),
            metrics.get("fuerza", 0)
        )

        # Calcular métricas adicionales
        consistency_score = calculate_consistency_score(metrics)
        movement_patterns = analyze_movement_patterns(metrics)
        stroke_effectiveness = calculate_stroke_effectiveness(metrics)

        response = {
            "metrics": {
                **metrics,
                "consistency_score": consistency_score,
                "movement_patterns": movement_patterns,
                "stroke_effectiveness": stroke_effectiveness
            },
            "force_category": force_category,
            "force_level": metrics.get("fuerza", 0),
            "padel_iq": padel_iq,
            "player_level": player_level
        }

        # Guardar el análisis en Firestore
        analysis_doc = {
            "video_id": video_id,
            "user_id": user_id,
            "video_url": str(video_url),
            "tipo_video": tipo_video,
            "metrics": response["metrics"],
            "padel_iq": padel_iq,
            "player_level": player_level,
            "force_category": force_category,
            "force_level": metrics.get("fuerza", 0),
            "created_at": firestore.SERVER_TIMESTAMP,
            "analysis_status": "completed",
            "analysis_completed_at": firestore.SERVER_TIMESTAMP
        }
        db.collection("video_analysis").document(video_id).set(analysis_doc)
        
        # Actualizar estado del video
        db.collection("videos").document(video_id).update({
            "analysis_status": "completed",
            "analysis_progress": 100,
            "analysis_completed_at": firestore.SERVER_TIMESTAMP
        })

        logger.info(f"Análisis guardado en Firestore con video_id: {video_id}")
        response["video_id"] = video_id
        return response

    except Exception as e:
        logger.error(f"Error calculating Padel IQ: {str(e)}")
        # Actualizar estado del video con el error
        db.collection("videos").document(video_id).update({
            "analysis_status": "error",
            "analysis_error": str(e),
            "analysis_completed_at": firestore.SERVER_TIMESTAMP
        })
        raise HTTPException(status_code=500, detail=f"Error calculating Padel IQ: {str(e)}")

def calculate_consistency_score(metrics: dict) -> float:
    """Calcula un score de consistencia basado en la variabilidad de las métricas."""
    # Implementación simulada
    return 75.0

def analyze_movement_patterns(metrics: dict) -> dict:
    """Analiza patrones de movimiento del jugador."""
    # Implementación simulada
    return {
        "court_coverage": metrics.get("court_coverage", 0),
        "movement_efficiency": 0.8,
        "recovery_speed": 0.7
    }

def calculate_stroke_effectiveness(metrics: dict) -> dict:
    """Calcula la efectividad por tipo de golpe."""
    # Implementación simulada
    return {
        "derecha": 0.8,
        "reves": 0.7,
        "volea": 0.75,
        "smash": 0.85
    }

# Endpoint para análisis asíncrono
@router.post("/analyze")
async def start_video_analysis(data: VideoAnalyzeRequest, current_user: UserInDB = Depends(get_current_user)):
    try:
        task = analyze_video.delay(data.user_id, str(data.video_url), data.tipo_video, data.player_position)
        logger.info(f"Análisis asíncrono iniciado para user_id: {data.user_id}, task_id: {task.id}")
        return {"task_id": task.id, "status": "pending", "message": "Análisis iniciado"}
    except Exception as e:
        logger.error(f"Error iniciando análisis asíncrono: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error iniciando análisis: {str(e)}")

@router.get("/analyze/{task_id}")
async def get_analysis_status(task_id: str, current_user: UserInDB = Depends(get_current_user)):
    try:
        task = analyze_video.AsyncResult(task_id)
        if task.state == "PENDING":
            return {"task_id": task_id, "status": "pending", "message": "Análisis en progreso"}
        elif task.state == "SUCCESS":
            result = task.result
            if isinstance(result, dict) and "error" in result:
                return {"task_id": task_id, "status": "failed", "error": result["error"]}
            return {"task_id": task_id, "status": "completed", "result": result}
        elif task.state == "FAILURE":
            return {"task_id": task_id, "status": "failed", "error": str(task.result)}
        else:
            return {"task_id": task_id, "status": task.state, "info": str(task.info)}
    except Exception as e:
        logger.error(f"Error consultando estado del análisis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error consultando estado: {str(e)}")

@router.get("/preview/{video_id}")
async def preview_video(
    video_id: str,
    current_user: UserInDB = Depends(get_current_user),
    start_time: int = Query(0, ge=0, description="Tiempo de inicio en segundos"),
    duration: int = Query(10, ge=1, le=30, description="Duración de la previsualización en segundos")
):
    """
    Genera una previsualización del video antes del análisis.
    - Permite especificar el tiempo de inicio y duración
    - Genera una versión de menor calidad para previsualización
    - Incluye metadatos básicos del video
    """
    try:
        db = get_db()
        video_doc = db.collection("videos").document(video_id).get()
        
        if not video_doc.exists:
            raise HTTPException(status_code=404, detail="Video no encontrado")
            
        video_data = video_doc.to_dict()
        
        # Verificar propiedad del video
        if video_data.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="No autorizado para ver este video")
            
        # Verificar si el video está disponible
        if video_data.get("status") not in ["uploaded", "processing", "completed"]:
            raise HTTPException(status_code=400, detail="Video no disponible para previsualización")
            
        # Obtener metadatos del video
        video_duration = video_data.get("duration_seconds", 0)
        if start_time >= video_duration:
            raise HTTPException(status_code=400, detail="Tiempo de inicio fuera de rango")
            
        # Ajustar duración si excede el final del video
        if start_time + duration > video_duration:
            duration = video_duration - start_time
            
        # Generar URL de previsualización
        preview_url = f"https://storage.padzr.com/previews/{video_id}_{start_time}_{duration}.mp4"
        
        # Generar thumbnail
        thumbnail_url = f"https://storage.padzr.com/thumbnails/{video_id}_{start_time}.jpg"
        
        return {
            "video_id": video_id,
            "preview_url": preview_url,
            "thumbnail_url": thumbnail_url,
            "start_time": start_time,
            "duration": duration,
            "original_duration": video_duration,
            "metadata": {
                "filename": video_data.get("filename"),
                "content_type": video_data.get("content_type"),
                "size_bytes": video_data.get("size_bytes"),
                "uploaded_at": video_data.get("uploaded_at")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al generar previsualización: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al generar previsualización")

@router.post("/analyze/{task_id}/retry")
async def retry_analysis(
    task_id: str,
    current_user: UserInDB = Depends(get_current_user),
    force: bool = Query(False, description="Forzar reintento incluso si el análisis no falló")
):
    """
    Reintenta un análisis de video que falló previamente.
    - Verifica el estado actual del análisis
    - Permite forzar el reintento si es necesario
    - Mantiene un registro de intentos
    """
    try:
        db = get_db()
        
        # Obtener información del análisis original
        analysis_doc = db.collection("video_analysis").document(task_id).get()
        if not analysis_doc.exists:
            raise HTTPException(status_code=404, detail="Análisis no encontrado")
            
        analysis_data = analysis_doc.to_dict()
        
        # Verificar propiedad del análisis
        if analysis_data.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="No autorizado para reintentar este análisis")
            
        # Verificar estado actual
        current_status = analysis_data.get("analysis_status")
        if current_status == "completed" and not force:
            raise HTTPException(
                status_code=400,
                detail="El análisis ya está completo. Use force=true para forzar el reintento."
            )
            
        # Verificar número de intentos
        retry_count = analysis_data.get("retry_count", 0)
        if retry_count >= 3 and not force:
            raise HTTPException(
                status_code=400,
                detail="Se ha alcanzado el límite de reintentos. Use force=true para forzar el reintento."
            )
            
        # Obtener datos del video
        video_id = analysis_data.get("video_id")
        video_doc = db.collection("videos").document(video_id).get()
        if not video_doc.exists:
            raise HTTPException(status_code=404, detail="Video no encontrado")
            
        video_data = video_doc.to_dict()
        
        # Preparar datos para el nuevo análisis
        analysis_request = VideoAnalyzeRequest(
            user_id=current_user.id,
            video_url=video_data.get("video_url"),
            tipo_video=analysis_data.get("tipo_video"),
            player_position=analysis_data.get("player_position", {"side": "left", "zone": "back"})
        )
        
        # Iniciar nuevo análisis
        new_task = analyze_video.delay(
            analysis_request.user_id,
            str(analysis_request.video_url),
            analysis_request.tipo_video,
            analysis_request.player_position
        )
        
        # Actualizar estado en la base de datos
        db.collection("video_analysis").document(task_id).update({
            "analysis_status": "retrying",
            "retry_count": retry_count + 1,
            "last_retry_at": firestore.SERVER_TIMESTAMP,
            "last_retry_task_id": new_task.id,
            "retry_history": firestore.ArrayUnion([{
                "task_id": new_task.id,
                "timestamp": firestore.SERVER_TIMESTAMP,
                "reason": "manual_retry" if force else "error_retry"
            }])
        })
        
        return {
            "task_id": new_task.id,
            "original_task_id": task_id,
            "status": "retrying",
            "retry_count": retry_count + 1,
            "message": "Análisis reiniciado correctamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al reintentar análisis: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al reintentar análisis")

# Ejemplo de uso en un endpoint:
# @router.get("/video/firestore_test")
# async def firestore_test(db: firestore.Client = Depends(get_db)):
#     # Aquí puedes usar db para acceder a Firestore
#     return {"message": "Firestore está disponible"} 