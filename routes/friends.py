from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from firebase_admin import firestore
from typing import List, Optional
import uuid
import logging
from datetime import datetime
from .auth import get_current_user

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/friends", tags=["Friends"])

class FriendRequest(BaseModel):
    proposer_id: str = Field(..., description="ID del usuario que envía la solicitud")
    receiver_id: str = Field(..., description="ID del usuario que recibe la solicitud")

class FriendshipResponse(BaseModel):
    friendship_id: str
    status: str
    timestamp: datetime
    user_id_1: str
    user_id_2: str

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

@router.post("/request", response_model=FriendshipResponse)
async def send_friend_request(
    request: FriendRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Envía una solicitud de amistad entre dos usuarios.
    """
    if request.proposer_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="No autorizado para enviar solicitudes en nombre de otro usuario")

    db = get_db()
    
    # Verificar si ya existe una solicitud pendiente
    existing_request = db.collection("friendships")\
        .where("user_id_1", "==", request.proposer_id)\
        .where("user_id_2", "==", request.receiver_id)\
        .where("status", "in", ["pending", "accepted"])\
        .get()
    
    if existing_request:
        raise HTTPException(status_code=400, detail="Ya existe una solicitud de amistad entre estos usuarios")

    friendship_id = str(uuid.uuid4())
    friendship = {
        "friendship_id": friendship_id,
        "user_id_1": request.proposer_id,
        "user_id_2": request.receiver_id,
        "status": "pending",
        "timestamp": firestore.SERVER_TIMESTAMP,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    try:
        db.collection("friendships").document(friendship_id).set(friendship)
        logger.info(f"Solicitud de amistad creada: {friendship_id}")
        return friendship
    except Exception as e:
        logger.error(f"Error al crear solicitud de amistad: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al crear la solicitud de amistad")

@router.post("/accept", response_model=FriendshipResponse)
async def accept_friend_request(
    request: FriendRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Acepta una solicitud de amistad pendiente.
    """
    if request.receiver_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="No autorizado para aceptar solicitudes en nombre de otro usuario")

    db = get_db()
    friendship = db.collection("friendships")\
        .where("user_id_1", "==", request.proposer_id)\
        .where("user_id_2", "==", request.receiver_id)\
        .where("status", "==", "pending")\
        .get()

    if not friendship:
        raise HTTPException(status_code=404, detail="Solicitud de amistad no encontrada")

    try:
        friendship_ref = friendship[0].reference
        friendship_data = friendship[0].to_dict()
        friendship_data["status"] = "accepted"
        friendship_data["updated_at"] = datetime.utcnow().isoformat()
        friendship_ref.update(friendship_data)
        
        logger.info(f"Solicitud de amistad aceptada: {friendship_data['friendship_id']}")
        return friendship_data
    except Exception as e:
        logger.error(f"Error al aceptar solicitud de amistad: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al aceptar la solicitud de amistad")

@router.get("/{user_id}", response_model=List[dict])
async def get_friends(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene la lista de amigos de un usuario.
    """
    if user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="No autorizado para ver amigos de otro usuario")

    db = get_db()
    try:
        # Obtener amigos donde el usuario es user_id_1
        friends_1 = db.collection("friendships")\
            .where("user_id_1", "==", user_id)\
            .where("status", "==", "accepted")\
            .get()
        
        # Obtener amigos donde el usuario es user_id_2
        friends_2 = db.collection("friendships")\
            .where("user_id_2", "==", user_id)\
            .where("status", "==", "accepted")\
            .get()

        friends = []
        for f in friends_1:
            friend_data = f.to_dict()
            friends.append({
                "user_id": friend_data["user_id_2"],
                "friendship_id": friend_data["friendship_id"],
                "since": friend_data["updated_at"]
            })
        
        for f in friends_2:
            friend_data = f.to_dict()
            friends.append({
                "user_id": friend_data["user_id_1"],
                "friendship_id": friend_data["friendship_id"],
                "since": friend_data["updated_at"]
            })

        logger.info(f"Amigos obtenidos para usuario {user_id}: {len(friends)}")
        return friends
    except Exception as e:
        logger.error(f"Error al obtener amigos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al obtener la lista de amigos")

@router.delete("/{friendship_id}")
async def remove_friendship(
    friendship_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Elimina una amistad existente.
    """
    db = get_db()
    try:
        friendship = db.collection("friendships").document(friendship_id).get()
        if not friendship.exists:
            raise HTTPException(status_code=404, detail="Amistad no encontrada")

        friendship_data = friendship.to_dict()
        if current_user["user_id"] not in [friendship_data["user_id_1"], friendship_data["user_id_2"]]:
            raise HTTPException(status_code=403, detail="No autorizado para eliminar esta amistad")

        db.collection("friendships").document(friendship_id).delete()
        logger.info(f"Amistad eliminada: {friendship_id}")
        return {"status": "success", "message": "Amistad eliminada correctamente"}
    except Exception as e:
        logger.error(f"Error al eliminar amistad: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al eliminar la amistad")

@router.get("/friends")
async def get_friends_endpoint(db: firestore.Client = Depends(get_db)):
    try:
        logger.info("Obteniendo información de amigos")
        # Aquí puedes usar db para acceder a Firestore
        return {"message": "Friends endpoint"}
    except Exception as e:
        logger.error(f"Error en friends: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en friends: {str(e)}") 