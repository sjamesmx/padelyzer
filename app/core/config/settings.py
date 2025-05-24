"""
Configuraciones de la aplicación basadas en Pydantic BaseSettings.

Este módulo define todas las configuraciones de la aplicación,
con valores predeterminados y validaciones.
"""
import os
from typing import Optional, Dict, Any, List
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    """Configuraciones de la aplicación."""

    # Configuración básica de la aplicación
    APP_NAME: str = "Padelyzer"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    TESTING: bool = os.getenv("TESTING", "False").lower() == "true"

    # Configuración de seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", "desarrollo_inseguro_no_usar_en_produccion")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 horas

    # Configuración de Firebase
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_PRIVATE_KEY_ID: str = os.getenv("FIREBASE_PRIVATE_KEY_ID", "")
    FIREBASE_PRIVATE_KEY: str = os.getenv("FIREBASE_PRIVATE_KEY", "")
    FIREBASE_CLIENT_EMAIL: str = os.getenv("FIREBASE_CLIENT_EMAIL", "")
    FIREBASE_CLIENT_ID: str = os.getenv("FIREBASE_CLIENT_ID", "")
    FIREBASE_CLIENT_CERT_URL: str = os.getenv("FIREBASE_CLIENT_CERT_URL", "")
    FIREBASE_STORAGE_BUCKET: str = os.getenv("FIREBASE_STORAGE_BUCKET", "")

    # Configuración de análisis de video
    MAX_VIDEO_SIZE_MB: int = int(os.getenv("MAX_VIDEO_SIZE_MB", "200"))
    SUPPORTED_VIDEO_FORMATS: List[str] = ["mp4", "mov", "avi"]

    # Configuración de procesamiento
    VIDEO_PROCESSING_BATCH_SIZE: int = int(os.getenv("VIDEO_PROCESSING_BATCH_SIZE", "10"))

    # Configuración de correo electrónico
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "True").lower() == "true"
    SMTP_PORT: Optional[int] = int(os.getenv("SMTP_PORT", "587"))
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST", "")
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD", "")
    EMAILS_FROM_EMAIL: Optional[str] = os.getenv("EMAILS_FROM_EMAIL", "")
    EMAILS_FROM_NAME: Optional[str] = os.getenv("EMAILS_FROM_NAME", "")

    @validator("SUPPORTED_VIDEO_FORMATS", pre=True)
    def validate_video_formats(cls, v):
        """Valida y prepara formatos de video soportados."""
        if isinstance(v, str):
            return [fmt.strip() for fmt in v.split(",")]
        return v

    class Config:
        """Configuraciones para Pydantic."""
        case_sensitive = True
        env_file = ".env"

# Instancia global de configuraciones
settings = Settings()
