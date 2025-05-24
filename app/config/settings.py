"""
Configuración centralizada de la aplicación.

Este módulo contiene todas las configuraciones de la aplicación,
obtenidas principalmente de variables de entorno.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List

class Settings(BaseSettings):
    # Configuración general
    PROJECT_NAME: str = "Padelyzer"
    DESCRIPTION: str = "API para análisis de videos de pádel"
    VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # JWT y Seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", "padelyzer_secret_key_for_development_only")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Firebase
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "padelyzer")
    FIREBASE_PRIVATE_KEY_ID: str = os.getenv("FIREBASE_PRIVATE_KEY_ID", "")
    FIREBASE_PRIVATE_KEY: str = os.getenv("FIREBASE_PRIVATE_KEY", "")
    FIREBASE_CLIENT_EMAIL: str = os.getenv("FIREBASE_CLIENT_EMAIL", "")
    FIREBASE_CLIENT_ID: str = os.getenv("FIREBASE_CLIENT_ID", "")
    FIREBASE_CLIENT_CERT_URL: str = os.getenv("FIREBASE_CLIENT_CERT_URL", "")
    FIREBASE_STORAGE_BUCKET: str = os.getenv(
        "FIREBASE_STORAGE_BUCKET",
        f"{os.getenv('FIREBASE_PROJECT_ID', 'padelyzer')}.appspot.com"
    )
    FIREBASE_CREDENTIALS: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_PATH")

    # Configuración para tests
    TESTING: bool = os.getenv("TESTING", "False") == "True"
    TEST_DATABASE: str = "test_database"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "https://padelyzer.vercel.app",
        "https://padelyzer.app"
    ]

    # API
    API_PREFIX: str = "/api"
    API_V1_PREFIX: str = "/api/v1"

    # Redis y tareas en segundo plano
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")

    # Logs
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Límites de archivos
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "200"))

    class Config:
        env_file = ".env"
        case_sensitive = True

# Crear instancia global de configuración
settings = Settings()
