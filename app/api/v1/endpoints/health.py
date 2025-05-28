"""
Endpoints para verificar el estado de salud de la aplicación.
"""

from fastapi import APIRouter, HTTPException
from app.core.config.firebase import get_health_status, verify_firebase_connection
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """
    Verifica el estado de salud general de la aplicación.
    """
    try:
        firebase_status = get_health_status()
        return {
            "status": "healthy" if firebase_status["status"] == "healthy" else "unhealthy",
            "components": {
                "firebase": firebase_status
            }
        }
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al verificar estado de salud: {str(e)}"
        )

@router.get("/health/firebase")
async def firebase_health_check():
    """
    Verifica específicamente el estado de salud de Firebase.
    """
    try:
        return get_health_status()
    except Exception as e:
        logger.error(f"Error en Firebase health check: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al verificar estado de Firebase: {str(e)}"
        ) 