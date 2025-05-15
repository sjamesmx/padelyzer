from fastapi import APIRouter, Depends, HTTPException
from firebase_admin import firestore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

@router.get("/onboarding")
async def get_onboarding(db: firestore.Client = Depends(get_db)):
    try:
        logger.info("Obteniendo información de onboarding")
        # Aquí puedes usar db para acceder a Firestore
        return {"message": "Onboarding del usuario"}
    except Exception as e:
        logger.error(f"Error en onboarding: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en onboarding: {str(e)}")