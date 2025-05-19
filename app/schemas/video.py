from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime
from enum import Enum

class VideoType(str, Enum):
    TRAINING = "training"
    GAME = "game"
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
    video_id: str
    analysis_type: str = Field(..., pattern='^(training|game)$')
    options: Optional[dict] = Field(default_factory=dict)

class VideoAnalysisResponse(BaseModel):
    id: str
    video_id: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    results: Optional[dict]
    error: Optional[str]

class VideoUpload(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    video_type: VideoType
    is_public: bool = False
    
    @validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('El título no puede estar vacío')
        return v

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

class VideoListResponse(BaseModel):
    videos: List[VideoResponse]
    total: int
    page: int
    page_size: int 