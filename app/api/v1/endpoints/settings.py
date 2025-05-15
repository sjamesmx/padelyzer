from fastapi import APIRouter, HTTPException, Depends
from firebase_admin import firestore
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
from typing import Optional, Dict
import logging

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

# Obtener preferencias del usuario
@router.get("/")
async def get_user_settings(current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    doc = db.collection("user_settings").document(current_user.id).get()
    if not doc.exists:
        # Valores por defecto
        return {
            "user_id": current_user.id,
            "notifications": True,
            "language": "es",
            "theme": "light"
        }
    return doc.to_dict()

# Actualizar preferencias del usuario
@router.put("/")
async def update_user_settings(
    notifications: Optional[bool] = None,
    language: Optional[str] = None,
    theme: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    db = get_db()
    doc_ref = db.collection("user_settings").document(current_user.id)
    updates = {}
    if notifications is not None:
        updates["notifications"] = notifications
    if language is not None:
        updates["language"] = language
    if theme is not None:
        updates["theme"] = theme
    if not updates:
        raise HTTPException(status_code=400, detail="No se proporcionaron cambios")
    updates["user_id"] = current_user.id
    doc_ref.set(updates, merge=True)
    return {"message": "Preferencias actualizadas", **updates} 