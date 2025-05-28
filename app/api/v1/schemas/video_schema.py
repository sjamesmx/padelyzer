from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
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

class VideoUploadRequest(BaseModel):
    filename: str = Field(..., min_length=1, description="Name of the video file")
    video_type: VideoType = Field(..., description="Type of video (training, game, torneo)")
    description: Optional[str] = Field(None, max_length=500, description="Optional description of the video")
    player_position: Optional[dict] = Field(None, description="Player position information")

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "my_video.mp4",
                "video_type": "training",
                "description": "Training session video",
                "player_position": {"side": "right", "zone": "back"}
            }
        }

class VideoUploadResponse(BaseModel):
    video_id: str = Field(..., description="Unique identifier for the uploaded video")
    url: str = Field(..., description="URL of the uploaded video in Firebase Storage")
    status: VideoStatus = Field(..., description="Current status of the video")
    created_at: datetime = Field(..., description="Timestamp when the video was uploaded")
    message: str = Field(..., description="Status message")
    padel_iq: Optional[float] = Field(None, description="Calculated Padel IQ")
    metrics: Optional[dict] = Field(None, description="Detailed metrics of the analysis")

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "video-123",
                "url": "https://firebasestorage.googleapis.com/v0/b/pdzr-458820.firebasestorage.app/o/videos/user123/video.mp4",
                "status": "pending",
                "created_at": "2024-05-19T10:00:00Z",
                "message": "Video uploaded successfully",
                "padel_iq": 85.5,
                "metrics": {
                    "tecnica": 90,
                    "ritmo": 80,
                    "fuerza": 85,
                    "total_golpes": 10,
                    "video_duration": 120,
                    "golpes_detallados": []
                }
            }
        } 