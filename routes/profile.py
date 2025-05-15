from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definir el router de FastAPI
router = APIRouter()

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

# Endpoint para obtener el perfil del usuario
@router.get("/profile")
async def get_profile(db: firestore.Client = Depends(get_db)):
    """Obtiene el perfil del usuario."""
    try:
        logger.info("Obteniendo perfil del usuario")
        # Aquí puedes usar db para acceder a Firestore
        return {
            "message": "Perfil del usuario",
            "user_id": "testuser",
            "email": "test@example.com",
            "level": "intermediate"
        }
    except Exception as e:
        logger.error(f"Error obteniendo el perfil: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo el perfil: {str(e)}")