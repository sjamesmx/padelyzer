from fastapi import APIRouter, HTTPException, Depends, status, Query
from firebase_admin import firestore
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid
import logging
from pydantic import BaseModel
from app.services.notifications import notification_service

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definición de logros
ACHIEVEMENTS = [
    {
        "achievement_id": "first_match",
        "name": "Primer partido",
        "description": "Juega tu primer partido",
        "points": 100,
        "icon": "🎾",
        "category": "matches"
    },
    {
        "achievement_id": "ten_matches",
        "name": "10 partidos",
        "description": "Juega 10 partidos",
        "points": 500,
        "icon": "🏆",
        "category": "matches"
    },
    {
        "achievement_id": "first_win",
        "name": "Primera victoria",
        "description": "Gana tu primer partido",
        "points": 200,
        "icon": "🌟",
        "category": "matches"
    },
    {
        "achievement_id": "first_analysis",
        "name": "Primer análisis",
        "description": "Sube tu primer video para análisis",
        "points": 150,
        "icon": "📊",
        "category": "analysis"
    },
    {
        "achievement_id": "pro_subscription",
        "name": "Pro",
        "description": "Suscríbete al plan Pro",
        "points": 1000,
        "icon": "💎",
        "category": "premium"
    },
    {
        "achievement_id": "social_butterfly",
        "name": "Mariposa social",
        "description": "Agrega 10 amigos",
        "points": 300,
        "icon": "🦋",
        "category": "social"
    }
]

# Definición de recompensas
REWARDS = [
    {
        "reward_id": "free_analysis",
        "name": "Análisis gratis",
        "description": "Obtén un análisis de video gratis",
        "points_cost": 500,
        "required_achievements": ["first_match"],
        "icon": "🎥",
        "category": "analysis"
    },
    {
        "reward_id": "discount_pro",
        "name": "Descuento Pro",
        "description": "20% de descuento en suscripción Pro",
        "points_cost": 1000,
        "required_achievements": ["ten_matches"],
        "icon": "💎",
        "category": "premium"
    },
    {
        "reward_id": "custom_racket",
        "name": "Personalización de pala",
        "description": "Personaliza el diseño de tu pala",
        "points_cost": 2000,
        "required_achievements": ["pro_subscription"],
        "icon": "🎨",
        "category": "premium"
    }
]

class AchievementProgress(BaseModel):
    achievement_id: str
    current_progress: int
    target: int
    completed: bool
    completed_at: Optional[datetime] = None

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

@router.get("/achievements", response_model=List[Dict], summary="Listar logros disponibles", tags=["gamification"])
async def get_achievements(
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Lista todos los logros disponibles.
    - Permite filtrar por categoría
    - Incluye información detallada de cada logro
    """
    try:
        achievements = ACHIEVEMENTS
        if category:
            achievements = [a for a in achievements if a["category"] == category]
            
        # Obtener progreso del usuario
        db = get_db()
        user_achievements = db.collection("user_achievements").document(current_user.id).get()
        unlocked = user_achievements.to_dict().get("achievements", []) if user_achievements.exists else []
        
        # Enriquecer con información de progreso
        for achievement in achievements:
            achievement["unlocked"] = achievement["achievement_id"] in unlocked
            
        return achievements
        
    except Exception as e:
        logger.error(f"Error al listar logros: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar logros"
        )

@router.post("/achievements/{achievement_id}/unlock", response_model=Dict, summary="Desbloquear logro", tags=["gamification"])
async def unlock_achievement(
    achievement_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Desbloquea un logro para el usuario.
    - Verifica requisitos
    - Otorga puntos
    - Envía notificación
    """
    try:
        db = get_db()
        
        # Validar logro
        achievement = next((a for a in ACHIEVEMENTS if a["achievement_id"] == achievement_id), None)
        if not achievement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Logro no encontrado"
            )
            
        # Verificar si ya está desbloqueado
        user_achievements = db.collection("user_achievements").document(current_user.id).get()
        unlocked = user_achievements.to_dict().get("achievements", []) if user_achievements.exists else []
        
        if achievement_id in unlocked:
            return {"message": "Logro ya desbloqueado", "achievement": achievement}
            
        # Desbloquear logro
        unlocked.append(achievement_id)
        db.collection("user_achievements").document(current_user.id).set({
            "user_id": current_user.id,
            "achievements": unlocked,
            "updated_at": datetime.now()
        }, merge=True)
        
        # Otorgar puntos
        user_points = db.collection("user_points").document(current_user.id).get()
        current_points = user_points.to_dict().get("points", 0) if user_points.exists else 0
        new_points = current_points + achievement["points"]
        
        db.collection("user_points").document(current_user.id).set({
            "user_id": current_user.id,
            "points": new_points,
            "updated_at": datetime.now()
        }, merge=True)
        
        # Registrar en historial
        history_id = str(uuid.uuid4())
        db.collection("achievement_history").document(history_id).set({
            "user_id": current_user.id,
            "achievement_id": achievement_id,
            "points_earned": achievement["points"],
            "created_at": datetime.now()
        })
        
        # Enviar notificación
        notification_service.create_notification(
            user_id=current_user.id,
            type="achievement_unlocked",
            title=f"¡Logro desbloqueado: {achievement['name']}!",
            message=f"Has ganado {achievement['points']} puntos",
            data={
                "achievement_id": achievement_id,
                "points_earned": achievement["points"],
                "total_points": new_points
            }
        )
        
        return {
            "message": "Logro desbloqueado",
            "achievement": achievement,
            "points_earned": achievement["points"],
            "total_points": new_points
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al desbloquear logro: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al desbloquear logro"
        )

@router.get("/achievements/{user_id}", response_model=Dict, summary="Ver logros de usuario", tags=["gamification"])
async def get_user_achievements(
    user_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtiene los logros desbloqueados de un usuario.
    - Incluye progreso detallado
    - Muestra puntos ganados
    """
    try:
        db = get_db()
        
        # Obtener logros desbloqueados
        user_achievements = db.collection("user_achievements").document(user_id).get()
        unlocked = user_achievements.to_dict().get("achievements", []) if user_achievements.exists else []
        
        # Obtener puntos
        user_points = db.collection("user_points").document(user_id).get()
        points = user_points.to_dict().get("points", 0) if user_points.exists else 0
        
        # Obtener historial de logros
        achievement_history = db.collection("achievement_history")\
            .where("user_id", "==", user_id)\
            .order_by("created_at", direction=firestore.Query.DESCENDING)\
            .limit(10)\
            .get()
            
        history = [h.to_dict() for h in achievement_history]
        
        # Calcular progreso por categoría
        categories = {}
        for achievement in ACHIEVEMENTS:
            category = achievement["category"]
            if category not in categories:
                categories[category] = {"total": 0, "unlocked": 0}
            categories[category]["total"] += 1
            if achievement["achievement_id"] in unlocked:
                categories[category]["unlocked"] += 1
                
        return {
            "user_id": user_id,
            "total_points": points,
            "unlocked_achievements": unlocked,
            "achievement_history": history,
            "category_progress": categories
        }
        
    except Exception as e:
        logger.error(f"Error al obtener logros de usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener logros de usuario"
        )

@router.get("/rewards", response_model=List[Dict], summary="Listar recompensas disponibles", tags=["gamification"])
async def get_rewards(
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Lista las recompensas disponibles.
    - Permite filtrar por categoría
    - Muestra requisitos y costos
    """
    try:
        rewards = REWARDS
        if category:
            rewards = [r for r in rewards if r["category"] == category]
            
        # Obtener logros y puntos del usuario
        db = get_db()
        user_achievements = db.collection("user_achievements").document(current_user.id).get()
        user_points = db.collection("user_points").document(current_user.id).get()
        
        unlocked = user_achievements.to_dict().get("achievements", []) if user_achievements.exists else []
        points = user_points.to_dict().get("points", 0) if user_points.exists else 0
        
        # Enriquecer con información de disponibilidad
        for reward in rewards:
            reward["available"] = (
                all(a in unlocked for a in reward["required_achievements"]) and
                points >= reward["points_cost"]
            )
            reward["can_afford"] = points >= reward["points_cost"]
            reward["has_requirements"] = all(a in unlocked for a in reward["required_achievements"])
            
        return rewards
        
    except Exception as e:
        logger.error(f"Error al listar recompensas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar recompensas"
        )

@router.post("/rewards/{reward_id}/claim", response_model=Dict, summary="Canjear recompensa", tags=["gamification"])
async def claim_reward(
    reward_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Canjea una recompensa.
    - Verifica requisitos y puntos
    - Descuenta puntos
    - Envía notificación
    """
    try:
        db = get_db()
        
        # Validar recompensa
        reward = next((r for r in REWARDS if r["reward_id"] == reward_id), None)
        if not reward:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recompensa no encontrada"
            )
            
        # Verificar logros requeridos
        user_achievements = db.collection("user_achievements").document(current_user.id).get()
        unlocked = user_achievements.to_dict().get("achievements", []) if user_achievements.exists else []
        
        if not all(a in unlocked for a in reward["required_achievements"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No cumples los requisitos para esta recompensa"
            )
            
        # Verificar puntos
        user_points = db.collection("user_points").document(current_user.id).get()
        points = user_points.to_dict().get("points", 0) if user_points.exists else 0
        
        if points < reward["points_cost"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No tienes suficientes puntos"
            )
            
        # Verificar si ya fue canjeada
        user_rewards = db.collection("user_rewards").document(current_user.id).get()
        claimed = user_rewards.to_dict().get("rewards", []) if user_rewards.exists else []
        
        if reward_id in claimed:
            return {"message": "Recompensa ya canjeada", "reward": reward}
            
        # Canjear recompensa
        claimed.append(reward_id)
        db.collection("user_rewards").document(current_user.id).set({
            "user_id": current_user.id,
            "rewards": claimed,
            "updated_at": datetime.now()
        }, merge=True)
        
        # Descontar puntos
        new_points = points - reward["points_cost"]
        db.collection("user_points").document(current_user.id).set({
            "user_id": current_user.id,
            "points": new_points,
            "updated_at": datetime.now()
        }, merge=True)
        
        # Registrar en historial
        history_id = str(uuid.uuid4())
        db.collection("reward_history").document(history_id).set({
            "user_id": current_user.id,
            "reward_id": reward_id,
            "points_spent": reward["points_cost"],
            "created_at": datetime.now()
        })
        
        # Enviar notificación
        notification_service.create_notification(
            user_id=current_user.id,
            type="reward_claimed",
            title=f"¡Recompensa canjeada: {reward['name']}!",
            message=f"Has gastado {reward['points_cost']} puntos",
            data={
                "reward_id": reward_id,
                "points_spent": reward["points_cost"],
                "remaining_points": new_points
            }
        )
        
        return {
            "message": "Recompensa canjeada",
            "reward": reward,
            "points_spent": reward["points_cost"],
            "remaining_points": new_points
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al canjear recompensa: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al canjear recompensa"
        )

@router.get("/progress/{user_id}", response_model=Dict, summary="Ver progreso de gamificación", tags=["gamification"])
async def get_gamification_progress(
    user_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtiene el progreso detallado de gamificación de un usuario.
    - Muestra logros y recompensas
    - Incluye estadísticas y puntos
    """
    try:
        db = get_db()
        
        # Obtener logros y recompensas
        user_achievements = db.collection("user_achievements").document(user_id).get()
        user_rewards = db.collection("user_rewards").document(user_id).get()
        user_points = db.collection("user_points").document(user_id).get()
        
        unlocked = user_achievements.to_dict().get("achievements", []) if user_achievements.exists else []
        claimed = user_rewards.to_dict().get("rewards", []) if user_rewards.exists else []
        points = user_points.to_dict().get("points", 0) if user_points.exists else 0
        
        # Calcular progreso total
        total_achievements = len(ACHIEVEMENTS)
        total_rewards = len(REWARDS)
        achievement_progress = int((len(unlocked) / total_achievements) * 100) if total_achievements else 0
        reward_progress = int((len(claimed) / total_rewards) * 100) if total_rewards else 0
        
        # Obtener historial reciente
        achievement_history = db.collection("achievement_history")\
            .where("user_id", "==", user_id)\
            .order_by("created_at", direction=firestore.Query.DESCENDING)\
            .limit(5)\
            .get()
            
        reward_history = db.collection("reward_history")\
            .where("user_id", "==", user_id)\
            .order_by("created_at", direction=firestore.Query.DESCENDING)\
            .limit(5)\
            .get()
            
        return {
            "user_id": user_id,
            "total_points": points,
            "achievement_progress": achievement_progress,
            "reward_progress": reward_progress,
            "unlocked_achievements": len(unlocked),
            "total_achievements": total_achievements,
            "claimed_rewards": len(claimed),
            "total_rewards": total_rewards,
            "recent_achievements": [h.to_dict() for h in achievement_history],
            "recent_rewards": [h.to_dict() for h in reward_history]
        }
        
    except Exception as e:
        logger.error(f"Error al obtener progreso: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener progreso"
        )

@router.get("/leaderboard", response_model=List[Dict], summary="Ver tabla de líderes", tags=["gamification"])
async def get_leaderboard(
    category: Optional[str] = Query(None, description="Categoría: points, achievements, matches"),
    time_frame: Optional[str] = Query("all", description="Período: week, month, all"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtiene la tabla de líderes.
    - Múltiples categorías y períodos
    - Incluye ranking del usuario actual
    """
    try:
        db = get_db()
        
        # Determinar fecha límite según período
        if time_frame == "week":
            start_date = datetime.now() - timedelta(days=7)
        elif time_frame == "month":
            start_date = datetime.now() - timedelta(days=30)
        else:
            start_date = None
            
        # Obtener rankings según categoría
        if category == "points":
            # Ranking por puntos totales
            query = db.collection("user_points").order_by("points", direction=firestore.Query.DESCENDING)
        elif category == "achievements":
            # Ranking por logros desbloqueados
            query = db.collection("user_achievements").order_by("achievement_count", direction=firestore.Query.DESCENDING)
        elif category == "matches":
            # Ranking por partidos ganados
            query = db.collection("user_stats").order_by("matches_won", direction=firestore.Query.DESCENDING)
        else:
            # Ranking por puntos por defecto
            query = db.collection("user_points").order_by("points", direction=firestore.Query.DESCENDING)
            
        # Aplicar filtro de fecha si es necesario
        if start_date:
            query = query.where("updated_at", ">=", start_date)
            
        # Obtener resultados
        results = query.limit(limit).offset(offset).get()
        
        # Enriquecer datos
        leaderboard = []
        for doc in results:
            data = doc.to_dict()
            user_id = data["user_id"]
            
            # Obtener información del usuario
            user_doc = db.collection("users").document(user_id).get()
            user_data = user_doc.to_dict() if user_doc.exists else {}
            
            entry = {
                "user_id": user_id,
                "username": user_data.get("username"),
                "name": user_data.get("name"),
                "profile_picture": user_data.get("profile_picture"),
                "points": data.get("points", 0),
                "achievement_count": data.get("achievement_count", 0),
                "matches_won": data.get("matches_won", 0)
            }
            leaderboard.append(entry)
            
        # Obtener posición del usuario actual
        user_position = None
        if category == "points":
            user_points = db.collection("user_points").document(current_user.id).get()
            if user_points.exists:
                points = user_points.to_dict().get("points", 0)
                user_position = db.collection("user_points")\
                    .where("points", ">", points)\
                    .count()\
                    .get()[0][0] + 1
                    
        return {
            "leaderboard": leaderboard,
            "user_position": user_position,
            "total": len(leaderboard),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error al obtener tabla de líderes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener tabla de líderes"
        ) 