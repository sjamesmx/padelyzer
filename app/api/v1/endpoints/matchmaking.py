from fastapi import APIRouter, HTTPException, Depends, status, Query, Body
from firebase_admin import firestore
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import uuid
import logging
from app.services.notifications import notification_service
from app.schemas.matchmaking import MatchRequest, MatchResponse, MatchStatus
from app.services.firebase import get_firebase_client

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

# Buscar partido
@router.post("/find_match")
async def find_match(level: Optional[str] = None, position: Optional[str] = None, current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    # Simulación: crear una búsqueda de partido
    search_id = str(uuid.uuid4())
    search_data = {
        "search_id": search_id,
        "user_id": current_user.id,
        "level": level,
        "position": position,
        "status": "searching",
        "created_at": firestore.SERVER_TIMESTAMP
    }
    db.collection("match_searches").document(search_id).set(search_data)
    # Buscar partidos compatibles (simulado)
    matches = db.collection("matches").where("status", "==", "open").get()
    available_matches = [m.to_dict() for m in matches]
    return {"message": "Búsqueda iniciada", "search_id": search_id, "available_matches": available_matches}

# Cancelar búsqueda
@router.delete("/find_match")
async def cancel_find_match(current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    # Buscar búsqueda activa
    searches = db.collection("match_searches").where("user_id", "==", current_user.id).where("status", "==", "searching").get()
    for s in searches:
        db.collection("match_searches").document(s.id).update({"status": "cancelled"})
    # Notificar a los jugadores de partidos abiertos donde esté este usuario
    matches = db.collection("matches").where("status", "==", "open").get()
    for match in matches:
        match_data = match.to_dict()
        players = match_data.get("players", [])
        if current_user.id in players:
            for player_id in players:
                if player_id != current_user.id:
                    notif_id = str(uuid.uuid4())
                    db.collection("notifications").document(notif_id).set({
                        "notification_id": notif_id,
                        "user_id": player_id,
                        "type": "match_cancelled",
                        "from_user_id": current_user.id,
                        "match_id": match.id,
                        "created_at": firestore.SERVER_TIMESTAMP,
                        "read": False
                    })
            # Opcional: remover al usuario del partido
            players = [pid for pid in players if pid != current_user.id]
            db.collection("matches").document(match.id).update({"players": players})
    return {"message": "Búsqueda cancelada"}

# Obtener partidos disponibles
@router.get("/get_matches")
async def get_matches(current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    matches = db.collection("matches").where("status", "==", "open").get()
    return [m.to_dict() for m in matches]

# Aceptar partido
@router.post("/accept/{match_id}")
async def accept_match(match_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    match = db.collection("matches").document(match_id).get()
    if not match.exists:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    match_data = match.to_dict()
    # Simulación: añadir usuario al partido
    players = match_data.get("players", [])
    if current_user.id in players:
        raise HTTPException(status_code=400, detail="Ya estás en este partido")
    players.append(current_user.id)
    db.collection("matches").document(match_id).update({"players": players})
    # Notificar a los demás jugadores que un nuevo jugador se ha unido
    for player_id in players:
        if player_id != current_user.id:
            notif_id = str(uuid.uuid4())
            db.collection("notifications").document(notif_id).set({
                "notification_id": notif_id,
                "user_id": player_id,
                "type": "match_joined",
                "from_user_id": current_user.id,
                "match_id": match_id,
                "created_at": firestore.SERVER_TIMESTAMP,
                "read": False
            })
    # Si el partido se llena (ejemplo: 4 jugadores), notificar a todos
    if len(players) == 4:
        for player_id in players:
            notif_id = str(uuid.uuid4())
            db.collection("notifications").document(notif_id).set({
                "notification_id": notif_id,
                "user_id": player_id,
                "type": "match_full",
                "match_id": match_id,
                "created_at": firestore.SERVER_TIMESTAMP,
                "read": False
            })
        db.collection("matches").document(match_id).update({"status": "full"})
    return {"message": "Te has unido al partido", "match_id": match_id, "players": players}

# Rechazar partido
@router.post("/reject/{match_id}")
async def reject_match(match_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    match = db.collection("matches").document(match_id).get()
    if not match.exists:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    match_data = match.to_dict()
    # Simulación: marcar como rechazado para el usuario
    db.collection("matches").document(match_id).update({f"rejected_{current_user.id}": True})
    # Notificar a los demás jugadores
    players = match_data.get("players", [])
    for player_id in players:
        if player_id != current_user.id:
            notif_id = str(uuid.uuid4())
            db.collection("notifications").document(notif_id).set({
                "notification_id": notif_id,
                "user_id": player_id,
                "type": "match_rejected",
                "from_user_id": current_user.id,
                "match_id": match_id,
                "created_at": firestore.SERVER_TIMESTAMP,
                "read": False
            })
    return {"message": "Has rechazado el partido", "match_id": match_id}

# Detalles de partido
@router.get("/{match_id}")
async def get_match_details(match_id: str, current_user: UserInDB = Depends(get_current_user)):
    db = get_db()
    match = db.collection("matches").document(match_id).get()
    if not match.exists:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    return match.to_dict()

@router.get("/matches")
async def get_matches_list():
    raise HTTPException(status_code=501, detail="Not Implemented")

@router.post("/create_match", response_model=dict, summary="Crear partido", tags=["matchmaking"])
async def create_match(
    level: str = Query(..., description="Nivel de juego requerido"),
    position: str = Query(..., description="Posición preferida"),
    date: datetime = Query(..., description="Fecha y hora del partido"),
    location: str = Query(..., description="Ubicación del partido"),
    max_players: int = Query(4, ge=2, le=4, description="Número máximo de jugadores"),
    notes: Optional[str] = Query(None, description="Notas adicionales"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Crea un nuevo partido.
    - Valida la fecha y hora.
    - Verifica disponibilidad del usuario.
    - Crea el partido y notifica a jugadores compatibles.
    """
    try:
        db = get_db()
        
        # Validar fecha
        if date < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha del partido debe ser futura"
            )
            
        # Verificar si el usuario ya tiene un partido en esa fecha
        existing_matches = db.collection("matches").where("players", "array_contains", current_user.id).get()
        for match in existing_matches:
            match_data = match.to_dict()
            match_date = match_data.get("date")
            if isinstance(match_date, datetime) and abs(match_date - date) < timedelta(hours=2):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya tienes un partido programado cerca de esta fecha"
                )
                
        # Crear partido
        match_id = str(uuid.uuid4())
        match_data = {
            "match_id": match_id,
            "creator_id": current_user.id,
            "level": level,
            "position": position,
            "date": date,
            "location": location,
            "max_players": max_players,
            "notes": notes,
            "status": "open",
            "players": [current_user.id],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        db.collection("matches").document(match_id).set(match_data)
        
        # Buscar jugadores compatibles
        compatible_players = db.collection("users")\
            .where("level", "==", level)\
            .where("preferred_position", "==", position)\
            .get()
            
        # Notificar a jugadores compatibles
        for player in compatible_players:
            player_data = player.to_dict()
            if player.id != current_user.id:
                notification_service.create_notification(
                    user_id=player.id,
                    type="new_match",
                    title="Nuevo partido disponible",
                    message=f"Se ha creado un nuevo partido que coincide con tus preferencias",
                    data={
                        "match_id": match_id,
                        "level": level,
                        "position": position,
                        "date": date.isoformat(),
                        "location": location
                    }
                )
                
        return {
            "message": "Partido creado exitosamente",
            "match_id": match_id,
            "match_data": match_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear partido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear partido"
        )

@router.post("/matches/{match_id}/message", response_model=dict, summary="Enviar mensaje en partido", tags=["matchmaking"])
async def send_match_message(
    match_id: str,
    message: str = Query(..., min_length=1, max_length=500, description="Contenido del mensaje"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Envía un mensaje en el chat del partido.
    - Verifica que el usuario sea parte del partido.
    - Guarda el mensaje y notifica a los demás jugadores.
    """
    try:
        db = get_db()
        
        # Verificar partido
        match_doc = db.collection("matches").document(match_id).get()
        if not match_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Partido no encontrado"
            )
            
        match_data = match_doc.to_dict()
        if current_user.id not in match_data.get("players", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No eres parte de este partido"
            )
            
        # Crear mensaje
        message_id = str(uuid.uuid4())
        message_data = {
            "message_id": message_id,
            "match_id": match_id,
            "user_id": current_user.id,
            "user_name": current_user.name,
            "content": message,
            "created_at": datetime.now()
        }
        
        db.collection("match_messages").document(message_id).set(message_data)
        
        # Notificar a los demás jugadores
        for player_id in match_data.get("players", []):
            if player_id != current_user.id:
                notification_service.create_notification(
                    user_id=player_id,
                    type="match_message",
                    title="Nuevo mensaje en el partido",
                    message=f"{current_user.name}: {message[:50]}...",
                    data={
                        "match_id": match_id,
                        "message_id": message_id,
                        "from_user_id": current_user.id
                    }
                )
                
        return {
            "message": "Mensaje enviado exitosamente",
            "message_id": message_id,
            "message_data": message_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al enviar mensaje: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar mensaje"
        )

@router.post("/matches/{match_id}/rate", response_model=dict, summary="Calificar oponentes", tags=["matchmaking"])
async def rate_opponents(
    match_id: str,
    ratings: Dict[str, int] = Body(..., description="Diccionario de calificaciones por jugador (1-5)"),
    comments: Optional[Dict[str, str]] = Body(None, description="Comentarios opcionales por jugador"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Califica a los oponentes después del partido.
    - Verifica que el partido haya terminado.
    - Valida las calificaciones.
    - Actualiza el perfil de los jugadores.
    """
    try:
        db = get_db()
        
        # Verificar partido
        match_doc = db.collection("matches").document(match_id).get()
        if not match_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Partido no encontrado"
            )
            
        match_data = match_doc.to_dict()
        if current_user.id not in match_data.get("players", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No eres parte de este partido"
            )
            
        if match_data.get("status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El partido aún no ha terminado"
            )
            
        # Validar calificaciones
        for player_id, rating in ratings.items():
            if player_id not in match_data.get("players", []):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Jugador {player_id} no es parte del partido"
                )
            if rating < 1 or rating > 5:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Las calificaciones deben estar entre 1 y 5"
                )
                
        # Crear calificaciones
        rating_id = str(uuid.uuid4())
        rating_data = {
            "rating_id": rating_id,
            "match_id": match_id,
            "rater_id": current_user.id,
            "ratings": ratings,
            "comments": comments or {},
            "created_at": datetime.now()
        }
        
        db.collection("match_ratings").document(rating_id).set(rating_data)
        
        # Actualizar perfiles de jugadores
        for player_id, rating in ratings.items():
            if player_id != current_user.id:
                # Obtener calificaciones existentes
                player_ratings = db.collection("match_ratings")\
                    .where("ratings." + player_id, "!=", None)\
                    .get()
                    
                total_ratings = len(player_ratings)
                current_avg = 0
                
                if total_ratings > 0:
                    current_avg = sum(r.to_dict()["ratings"][player_id] for r in player_ratings) / total_ratings
                    
                # Calcular nueva media
                new_avg = ((current_avg * total_ratings) + rating) / (total_ratings + 1)
                
                # Actualizar perfil
                db.collection("users").document(player_id).update({
                    "rating": new_avg,
                    "total_ratings": total_ratings + 1,
                    "updated_at": datetime.now()
                })
                
                # Notificar al jugador
                notification_service.create_notification(
                    user_id=player_id,
                    type="match_rating",
                    title="Nueva calificación recibida",
                    message=f"Has recibido una calificación de {rating}/5 en tu último partido",
                    data={
                        "match_id": match_id,
                        "rating": rating,
                        "comment": comments.get(player_id) if comments else None
                    }
                )
                
        return {
            "message": "Calificaciones enviadas exitosamente",
            "rating_id": rating_id,
            "rating_data": rating_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al calificar oponentes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al calificar oponentes"
        )

@router.post("/request", response_model=MatchResponse)
async def create_match_request(
    request: MatchRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """Crea una solicitud de partido."""
    try:
        db = get_firebase_client()
        match_ref = db.collection('match_requests').document()
        
        match_data = request.dict()
        match_data.update({
            'user_id': current_user.id,
            'status': MatchStatus.PENDING,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        
        match_ref.set(match_data)
        
        return MatchResponse(
            id=match_ref.id,
            **match_data
        )
    except Exception as e:
        logger.error(f"Error al crear solicitud de partido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear solicitud de partido"
        )

@router.get("/requests", response_model=List[MatchResponse])
async def get_match_requests(
    current_user: UserInDB = Depends(get_current_user),
    status: Optional[MatchStatus] = None
):
    """Obtiene las solicitudes de partido."""
    try:
        db = get_firebase_client()
        query = db.collection('match_requests')
        
        if status:
            query = query.where('status', '==', status)
            
        requests = query.get()
        
        return [
            MatchResponse(id=doc.id, **doc.to_dict())
            for doc in requests
        ]
    except Exception as e:
        logger.error(f"Error al obtener solicitudes de partido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener solicitudes de partido"
        )

@router.put("/request/{request_id}/accept")
async def accept_match_request(
    request_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Acepta una solicitud de partido."""
    try:
        db = get_firebase_client()
        request_ref = db.collection('match_requests').document(request_id)
        request_doc = request_ref.get()
        
        if not request_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada"
            )
            
        request_data = request_doc.to_dict()
        
        if request_data['status'] != MatchStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La solicitud ya no está pendiente"
            )
            
        request_ref.update({
            'status': MatchStatus.ACCEPTED,
            'accepted_by': current_user.id,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        
        return {"message": "Solicitud aceptada"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al aceptar solicitud de partido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al aceptar solicitud de partido"
        )

@router.put("/request/{request_id}/reject")
async def reject_match_request(
    request_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Rechaza una solicitud de partido."""
    try:
        db = get_firebase_client()
        request_ref = db.collection('match_requests').document(request_id)
        request_doc = request_ref.get()
        
        if not request_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada"
            )
            
        request_data = request_doc.to_dict()
        
        if request_data['status'] != MatchStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La solicitud ya no está pendiente"
            )
            
        request_ref.update({
            'status': MatchStatus.REJECTED,
            'rejected_by': current_user.id,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        
        return {"message": "Solicitud rechazada"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al rechazar solicitud de partido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al rechazar solicitud de partido"
        ) 