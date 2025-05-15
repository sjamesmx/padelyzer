from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
import secrets
from functools import lru_cache
import firebase_admin
from firebase_admin import credentials, firestore

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "PDZR API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DESCRIPTION: str = "API para el análisis de pádel y gestión de usuarios"
    # Environment
    ENVIRONMENT: str = "development"
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_DATABASE_URL: Optional[str] = None
    FIREBASE_CRED_PATH: Optional[str] = os.getenv("FIREBASE_CRED_PATH", "firebase-service-account.json")
    FIREBASE_STORAGE_BUCKET: str = "pdzr-458820.firebasestorage.app"
    
    # JWT
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Security
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 100
    
    # Video Analysis
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "video/quicktime", "video/x-msvideo"]
    MAX_VIDEO_SIZE_MB: int = 100
    VIDEO_ANALYSIS_TIMEOUT: int = 300  # 5 minutos
    VIDEO_FRAME_RATE: int = 30
    VIDEO_QUALITY: str = "medium"  # low, medium, high
    VIDEO_RESOLUTION: Dict[str, int] = {
        "width": 1280,
        "height": 720
    }
    VIDEO_CODEC: str = "h264"
    VIDEO_FORMAT: str = "mp4"
    VIDEO_ANALYSIS_RETRY_COUNT: int = 3
    VIDEO_ANALYSIS_RETRY_DELAY: int = 60  # segundos
    
    # Storage
    UPLOAD_FOLDER: str = "uploads"
    TEMP_FOLDER: str = "temp"
    STORAGE_BASE_PATH: str = "videos"
    STORAGE_PATHS: Dict[str, str] = {
        "videos": "videos",
        "thumbnails": "thumbnails",
        "analysis": "analysis"
    }
    
    # Cache
    CACHE_TTL: int = 3600  # 1 hora
    
    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 3600  # 1 hora
    CELERY_TASK_SOFT_TIME_LIMIT: int = 3300  # 55 minutos
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 50
    CELERY_TASK_ACKS_LATE: bool = True
    CELERY_TASK_REJECT_ON_WORKER_LOST: bool = True
    CELERY_TASK_DEFAULT_QUEUE: str = "default"
    CELERY_TASK_QUEUES: Dict[str, Dict[str, str]] = {
        "default": {
            "exchange": "default",
            "routing_key": "default",
        },
        "video_analysis": {
            "exchange": "video_analysis",
            "routing_key": "video_analysis",
        }
    }
    CELERY_TASK_ROUTES: Dict[str, Dict[str, str]] = {
        "app.tasks.analyze_video": {
            "queue": "video_analysis",
            "routing_key": "video_analysis",
        }
    }
    
    # Notifications
    NOTIFICATION_TYPES: Dict[str, Dict[str, Any]] = {
        "video_analysis_complete": {
            "title": "Análisis de video completado",
            "message": "El análisis de tu video ha sido completado exitosamente."
        },
        "video_analysis_failed": {
            "title": "Error en el análisis de video",
            "message": "Ha ocurrido un error durante el análisis de tu video."
        }
    }
    
    # Error Handling
    ERROR_MESSAGES: Dict[str, str] = {
        "video_analysis_failed": "No se pudo completar el análisis del video",
        "video_download_failed": "No se pudo descargar el video",
        "video_processing_failed": "Error al procesar el video",
        "notification_failed": "Error al enviar la notificación"
    }
    
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "allow"
    }

settings = Settings() 