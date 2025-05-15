from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime
from enum import Enum

class VideoType(str, Enum):
    ENTRENAMIENTO = "entrenamiento"
    JUEGO = "juego"
    TORNEO = "torneo"

class VideoStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: VideoType
    player_position: Optional[Dict[str, Any]] = None

class VideoCreate(VideoBase):
    url: HttpUrl

class VideoInDB(VideoBase):
    id: str
    user_id: str
    url: str
    created_at: datetime
    status: VideoStatus
    analysis_result: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class VideoResponse(VideoInDB):
    pass

class VideoAnalysisRequest(BaseModel):
    user_id: str
    video_url: HttpUrl
    tipo_video: VideoType
    player_position: Dict[str, Any]

class VideoAnalysisResponse(BaseModel):
    analysis_id: str
    status: VideoStatus
    message: str

class VideoUpload(BaseModel):
    tipo_video: VideoType
    descripcion: Optional[str] = None

class VideoAnalysis(BaseModel):
    id: str
    user_id: str
    video_url: str
    tipo_video: VideoType
    fecha_analisis: datetime
    estado: VideoStatus
    resultados: Optional[dict] = None
    preview_frames: Optional[List[str]] = None
    blueprint: str
    error: Optional[str] = None 