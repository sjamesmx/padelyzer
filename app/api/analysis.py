from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from app.services.firebase import get_firebase_client
from google.cloud import firestore

router = APIRouter(prefix="/analysis", tags=["analysis"])

class KeypointsStats(BaseModel):
    avg_pose_accuracy: Optional[float]
    missed_frames: Optional[int]

class Metrics(BaseModel):
    padel_iq: float
    technique: float
    rhythm: float
    strength: float
    coverage: float
    shots: int
    stroke_types: Dict[str, int]
    stroke_confidences: Optional[Dict[str, float]]
    biomechanics: Optional[Dict[str, float]]
    stroke_interval_std: Optional[float]
    avg_wrist_speed: Optional[float]
    transition_smoothness: Optional[float]
    ball_speed_avg: Optional[float]
    ball_speed_max: Optional[float]
    torso_rotation_avg: Optional[float]
    jump_height_avg: Optional[float]
    power_stroke_ratio: Optional[float]
    distance_covered: float
    net_coverage_ratio: Optional[float]
    baseline_coverage_ratio: Optional[float]
    reaction_time: Optional[float]
    heatmap_url: Optional[str]
    keypoints_stats: Optional[KeypointsStats]

class Comparative(BaseModel):
    vs_personal_best: Optional[Dict[str, Any]]
    vs_global_avg: Optional[Dict[str, Any]]

class HistoryRef(BaseModel):
    analysis_id: str
    created_at: datetime
    padel_iq: float
    video_type: Optional[str]

class AnalysisResponse(BaseModel):
    analysis_id: str
    user_id: str
    status: str
    created_at: datetime
    video_type: str
    court_position: Optional[str]
    metrics: Metrics
    comparative: Optional[Comparative]
    history_refs: Optional[List[HistoryRef]]
    error_message: Optional[str]
    formula_version: Optional[str] = "1.0"

class StatusResponse(BaseModel):
    analysis_id: str
    status: str
    progress: Optional[float]
    error_message: Optional[str]

class UserHistoryResponse(BaseModel):
    user_id: str
    analyses: List[HistoryRef]

@router.get("/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: str):
    """Devuelve el resultado completo de un análisis de video desde Firestore."""
    db = get_firebase_client()
    doc = db.collection('video_analyses').document(analysis_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    data = doc.to_dict()
    # Adaptar los campos a los modelos
    metrics = Metrics(**data['metrics'])
    comparative = Comparative(**data['comparative']) if 'comparative' in data else None
    history_refs = [HistoryRef(**h) for h in data.get('history_refs', [])]
    return AnalysisResponse(
        analysis_id=analysis_id,
        user_id=data['user_id'],
        status=data.get('status', 'done'),
        created_at=data.get('created_at', datetime.utcnow()),
        video_type=data.get('video_type', 'match'),
        court_position=data.get('court_position'),
        metrics=metrics,
        comparative=comparative,
        history_refs=history_refs,
        error_message=data.get('error_message'),
        formula_version=data.get('formula_version', '1.0')
    )

@router.get("/{analysis_id}/metrics", response_model=Metrics)
def get_metrics(analysis_id: str):
    """Devuelve solo las métricas detalladas de un análisis desde Firestore."""
    db = get_firebase_client()
    doc = db.collection('video_analyses').document(analysis_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    data = doc.to_dict()
    return Metrics(**data['metrics'])

@router.get("/{analysis_id}/status", response_model=StatusResponse)
def get_status(analysis_id: str):
    """Devuelve el estado y progreso de un análisis desde Firestore."""
    db = get_firebase_client()
    doc = db.collection('video_analyses').document(analysis_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    data = doc.to_dict()
    return StatusResponse(
        analysis_id=analysis_id,
        status=data.get('status', 'pending'),
        progress=data.get('progress'),
        error_message=data.get('error_message')
    )

from fastapi import APIRouter as UserAPIRouter
user_router = UserAPIRouter(prefix="/users", tags=["users"])

@user_router.get("/{user_id}/history", response_model=UserHistoryResponse)
def user_history(user_id: str):
    """Devuelve el historial de análisis de un usuario desde Firestore."""
    db = get_firebase_client()
    # Buscar historial en padel_iq_history
    query = db.collection('padel_iq_history').where('user_id', '==', user_id).order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
    analyses = []
    for doc in query:
        d = doc.to_dict()
        analyses.append(HistoryRef(
            analysis_id=doc.id,
            created_at=d.get('timestamp', datetime.utcnow()),
            padel_iq=d.get('padel_iq', 0),
            video_type=d.get('tipo_analisis', 'match')
        ))
    return UserHistoryResponse(user_id=user_id, analyses=analyses) 