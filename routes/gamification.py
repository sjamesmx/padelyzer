from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from firebase_admin import firestore
from typing import List, Optional, Dict
import logging
from datetime import datetime
from .auth import get_current_user
import uuid

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gamification", tags=["Gamification"])

class Achievement(BaseModel):
    id: str
    name: str
    description: str
    points: int
    icon_url: str
    unlocked_at: Optional[datetime]

class Badge(BaseModel):
    id: str
    name: str
    description: str
    icon_url: str
    unlocked_at: Optional[datetime]

class GamificationResponse(BaseModel):
    points: int
    level: int
    badges: List[Badge]
    achievements: List[Achievement]
    next_level_points: int
    current_level_points: int

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

@router.get("/{user_id}", response_model=GamificationResponse)
async def get_gamification(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: firestore.Client = Depends(get_db)
):
    """
    Obtiene el estado de gamificación de un usuario.
    """
    if user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="No autorizado para ver gamificación de otro usuario")

    try:
        gamification = db.collection("gamification").document(user_id).get()
        
        if not gamification.exists:
            # Crear perfil de gamificación inicial
            initial_data = {
                "points": 0,
                "level": 1,
                "badges": [],
                "achievements": [],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            db.collection("gamification").document(user_id).set(initial_data)
            gamification_data = initial_data
        else:
            gamification_data = gamification.to_dict()

        # Calcular puntos necesarios para el siguiente nivel
        next_level_points = calculate_next_level_points(gamification_data["level"])
        current_level_points = calculate_current_level_points(gamification_data["level"])

        return {
            **gamification_data,
            "next_level_points": next_level_points,
            "current_level_points": current_level_points
        }
    except Exception as e:
        logger.error(f"Error al obtener gamificación: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener datos de gamificación")

@router.post("/{user_id}/add_points")
async def add_points(
    user_id: str,
    points: int = Field(..., gt=0),
    reason: str = Field(..., min_length=1),
    current_user: dict = Depends(get_current_user),
    db: firestore.Client = Depends(get_db)
):
    """
    Añade puntos a un usuario y actualiza su nivel si es necesario.
    """
    if user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="No autorizado para añadir puntos a otro usuario")

    try:
        gamification_ref = db.collection("gamification").document(user_id)
        gamification = gamification_ref.get()

        if not gamification.exists:
            raise HTTPException(status_code=404, detail="Perfil de gamificación no encontrado")

        gamification_data = gamification.to_dict()
        new_points = gamification_data["points"] + points
        current_level = gamification_data["level"]
        
        # Calcular nuevo nivel
        new_level = calculate_level(new_points)
        
        # Registrar la transacción de puntos
        transaction_id = str(uuid.uuid4())
        db.collection("point_transactions").document(transaction_id).set({
            "user_id": user_id,
            "points": points,
            "reason": reason,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "previous_points": gamification_data["points"],
            "new_points": new_points
        })

        # Actualizar gamificación
        update_data = {
            "points": new_points,
            "level": new_level,
            "updated_at": datetime.utcnow().isoformat()
        }

        # Si subió de nivel, registrar el log
        if new_level > current_level:
            update_data["level_up_log"] = firestore.ArrayUnion([{
                "from_level": current_level,
                "to_level": new_level,
                "timestamp": datetime.utcnow().isoformat()
            }])

        gamification_ref.update(update_data)
        
        logger.info(f"Puntos añadidos a usuario {user_id}: {points}")
        return {
            "status": "success",
            "new_points": new_points,
            "new_level": new_level,
            "level_up": new_level > current_level
        }
    except Exception as e:
        logger.error(f"Error al añadir puntos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al añadir puntos")

@router.get("/{user_id}/achievements")
async def get_achievements(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: firestore.Client = Depends(get_db)
):
    """
    Obtiene los logros disponibles y desbloqueados del usuario.
    """
    if user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="No autorizado para ver logros de otro usuario")

    try:
        # Obtener logros del usuario
        user_achievements = db.collection("gamification").document(user_id).get()
        user_achievements_data = user_achievements.to_dict() if user_achievements.exists else {"achievements": []}

        # Obtener todos los logros disponibles
        available_achievements = db.collection("achievements").get()
        available_achievements_data = [a.to_dict() for a in available_achievements]

        # Combinar información
        achievements = []
        for achievement in available_achievements_data:
            user_achievement = next(
                (a for a in user_achievements_data["achievements"] if a["id"] == achievement["id"]),
                None
            )
            achievements.append({
                **achievement,
                "unlocked": user_achievement is not None,
                "unlocked_at": user_achievement["unlocked_at"] if user_achievement else None
            })

        return achievements
    except Exception as e:
        logger.error(f"Error al obtener logros: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener logros")

def calculate_level(points: int) -> int:
    """Calcula el nivel basado en los puntos."""
    return max(1, (points // 1000) + 1)

def calculate_next_level_points(current_level: int) -> int:
    """Calcula los puntos necesarios para el siguiente nivel."""
    return current_level * 1000

def calculate_current_level_points(current_level: int) -> int:
    """Calcula los puntos necesarios para el nivel actual."""
    return (current_level - 1) * 1000 