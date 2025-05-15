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

# Métricas generales del usuario
@router.get("/metrics")
async def get_general_metrics(current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    user_id = current_user.id
    # Videos analizados
    videos = db.collection("video_analysis").where("user_id", "==", user_id).get()
    # Amigos
    friendships = db.collection("friendships").where("user_id_1", "==", user_id).get()
    friendships += db.collection("friendships").where("user_id_2", "==", user_id).get()
    # Posts
    posts = db.collection("posts").where("user_id", "==", user_id).get()
    # Partidos (simulado)
    matches = db.collection("matches").where("players", "array_contains", user_id).get()
    return {
        "user_id": user_id,
        "videos_analysed": len(videos),
        "friends": len(friendships),
        "posts": len(posts),
        "matches": len(matches)
    }

# Métricas de videos
@router.get("/metrics/videos")
async def get_video_metrics(current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    user_id = current_user.id
    videos = db.collection("video_analysis").where("user_id", "==", user_id).get()
    total = len(videos)
    avg_padel_iq = sum(v.to_dict().get("padel_iq", 0) for v in videos) / total if total else 0
    best = max((v.to_dict().get("padel_iq", 0) for v in videos), default=0)
    return {
        "total_videos": total,
        "average_padel_iq": avg_padel_iq,
        "best_padel_iq": best
    }

# Métricas sociales
@router.get("/metrics/social")
async def get_social_metrics(current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    user_id = current_user.id
    posts = db.collection("posts").where("user_id", "==", user_id).get()
    likes = db.collection("likes").where("user_id", "==", user_id).get()
    comments = db.collection("comments").where("user_id", "==", user_id).get()
    return {
        "posts": len(posts),
        "likes": len(likes),
        "comments": len(comments)
    }

# Personalización del dashboard
@router.get("/settings")
async def get_dashboard_settings(current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    doc = db.collection("dashboard_settings").document(current_user.id).get()
    if not doc.exists:
        return {"user_id": current_user.id, "widgets": ["metrics", "videos", "social"]}
    return doc.to_dict()

@router.put("/settings")
async def update_dashboard_settings(widgets: Optional[list] = None, current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    if widgets is None:
        widgets = ["metrics", "videos", "social"]
    db.collection("dashboard_settings").document(current_user.id).set({
        "user_id": current_user.id,
        "widgets": widgets
    })
    return {"message": "Configuración actualizada", "widgets": widgets}

@router.get("/dashboard")
async def get_dashboard(db: firestore.Client = Depends(get_db)):
    try:
        logger.info("Obteniendo dashboard")
        # Aquí puedes usar db para acceder a Firestore
        return {"message": "Dashboard del usuario"}
    except Exception as e:
        logger.error(f"Error obteniendo el dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo el dashboard: {str(e)}") 