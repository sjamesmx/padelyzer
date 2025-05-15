from fastapi import APIRouter, Depends, HTTPException, Request
import logging
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from services.notification_service import send_notification

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matchmaking", tags=["matchmaking"])

class MatchRequest(BaseModel):
    user_id: str
    skill_level: int
    preferred_time: Optional[datetime] = None
    location: Optional[str] = None

class MatchResponse(BaseModel):
    match_id: str
    status: str
    players: List[str]
    created_at: datetime

def get_db():
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

def calculate_distance(loc1, loc2):
    """Calcula la distancia aproximada entre dos ubicaciones (latitud, longitud)."""
    if not loc1 or not loc2 or 'latitude' not in loc1 or 'longitude' not in loc1 or 'latitude' not in loc2 or 'longitude' not in loc2:
        return float('inf')
    lat1, lon1 = loc1['latitude'], loc1['longitude']
    lat2, lon2 = loc2['latitude'], loc2['longitude']
    # Fórmula simplificada para distancia (aproximada, sin usar haversine)
    distance = ((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2) ** 0.5
    return distance

@router.get("/matchmaking")
async def get_matchmaking(db: firestore.Client = Depends(get_db)):
    try:
        logger.info("Obteniendo información de matchmaking")
        return {"message": "Matchmaking del usuario"}
    except Exception as e:
        logger.error(f"Error en matchmaking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en matchmaking: {str(e)}")

@router.post("/find", response_model=MatchResponse)
async def find_match(request: MatchRequest):
    # Implementación del matchmaking
    return MatchResponse(
        match_id="temp_id",
        status="pending",
        players=[request.user_id],
        created_at=datetime.now()
    )

@router.get("/status/{match_id}")
async def get_match_status(match_id: str):
    # Implementación del status
    return {"status": "pending", "match_id": match_id}

@router.post("/find_matches")
async def find_matches(request: Request, db: firestore.Client = Depends(get_db)):
    """Encuentra jugadores compatibles para un partido."""
    data = await request.json()
    user_id = data.get('user_id')
    max_distance = data.get('max_distance', 10.0)

    if not user_id:
        raise HTTPException(status_code=400, detail="Falta user_id")

    # Obtener datos del usuario
    user_ref = db.collection('users').document(user_id)
    user = user_ref.get()
    if not user.exists:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_data = user.to_dict()

    padel_iq = user_data.get('padel_iq')
    if padel_iq is None:
        raise HTTPException(status_code=400, detail="El usuario no tiene Padel IQ asignado")

    user_clubs = user_data.get('clubs', [])
    user_availability = user_data.get('availability', [])
    user_location = user_data.get('location', {})

    # Normalizar clubes y horarios
    user_clubs = [club.strip().lower() for club in user_clubs]
    user_availability = [avail.strip().lower() for avail in user_availability]

    logger.info(f"Usuario {user_id}: Padel IQ={padel_iq}, Clubes={user_clubs}, Disponibilidad={user_availability}, Ubicación={user_location}")

    # Buscar usuarios compatibles
    users = db.collection('users').where(filter=FieldFilter('onboarding_status', '==', 'completed')).get()
    compatible_users = []

    for other_user in users:
        if other_user.id == user_id:
            continue

        other_data = other_user.to_dict()
        other_padel_iq = other_data.get('padel_iq')
        if other_padel_iq is None:
            continue

        # Criterios de compatibilidad
        padel_iq_diff = abs(padel_iq - other_padel_iq)
        if padel_iq_diff > 5:
            continue

        other_clubs = other_data.get('clubs', [])
        other_clubs = [club.strip().lower() for club in other_clubs]
        common_clubs = set(user_clubs).intersection(other_clubs)
        if not common_clubs:
            continue

        other_availability = other_data.get('availability', [])
        other_availability = [avail.strip().lower() for avail in other_availability]
        common_availability = set(user_availability).intersection(other_availability)
        if not common_availability:
            continue

        other_location = other_data.get('location', {})
        distance = calculate_distance(user_location, other_location)
        if distance > max_distance:
            continue

        compatible_users.append({
            'user_id': other_user.id,
            'padel_iq': other_padel_iq,
            'clubs': list(common_clubs),
            'availability': list(common_availability),
            'distance': distance
        })

    compatible_users.sort(key=lambda x: abs(x['padel_iq'] - padel_iq))
    logger.info(f"Encontrados {len(compatible_users)} usuarios compatibles para {user_id}")
    return {"compatible_users": compatible_users}

@router.post("/send_request")
async def send_request(request: Request, db: firestore.Client = Depends(get_db)):
    """Envía una solicitud de partido a otro usuario."""
    data = await request.json()
    user_id = data.get('user_id')
    target_user_id = data.get('target_user_id')
    club = data.get('club')
    schedule = data.get('schedule')

    if not all([user_id, target_user_id, club, schedule]):
        raise HTTPException(status_code=400, detail="Faltan datos requeridos")

    user_ref = db.collection('users').document(user_id)
    user = user_ref.get()
    if not user.exists:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    target_user_ref = db.collection('users').document(target_user_id)
    target_user = target_user_ref.get()
    if not target_user.exists:
        raise HTTPException(status_code=404, detail="Usuario objetivo no encontrado")

    match_request_ref = db.collection('match_requests').document()
    match_request_ref.set({
        'from_user_id': user_id,
        'to_user_id': target_user_id,
        'club': club,
        'schedule': schedule,
        'status': 'pending',
        'timestamp': firestore.SERVER_TIMESTAMP
    })

    await send_notification(target_user_id, f"Tienes una nueva solicitud de partido de {user_id} para el {schedule} en {club}. ¿Aceptas?")

    logger.info(f"Solicitud de partido enviada de {user_id} a {target_user_id}")
    return {"message": "Solicitud de partido enviada exitosamente"}

@router.post("/respond_request")
async def respond_request(request: Request, db: firestore.Client = Depends(get_db)):
    """Responde a una solicitud de partido (aceptar o rechazar)."""
    data = await request.json()
    user_id = data.get('user_id')
    request_id = data.get('request_id')
    response = data.get('response')

    if not all([user_id, request_id, response]):
        raise HTTPException(status_code=400, detail="Faltan datos requeridos")

    if response not in ['accept', 'reject']:
        raise HTTPException(status_code=400, detail="Respuesta no válida")

    request_ref = db.collection('match_requests').document(request_id)
    request_doc = request_ref.get()
    if not request_doc.exists:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    request_data = request_doc.to_dict()
    if request_data['to_user_id'] != user_id:
        raise HTTPException(status_code=403, detail="No tienes permiso para responder a esta solicitud")

    if request_data['status'] != 'pending':
        raise HTTPException(status_code=400, detail="Esta solicitud ya ha sido respondida")

    request_ref.update({'status': response})

    from_user_id = request_data['from_user_id']
    club = request_data['club']
    schedule = request_data['schedule']
    
    if response == 'accept':
        await send_notification(from_user_id, f"{user_id} ha aceptado tu solicitud de partido para el {schedule} en {club}.")
        match_ref = db.collection('matches').document()
        match_ref.set({
            'user1_id': from_user_id,
            'user2_id': user_id,
            'club': club,
            'schedule': schedule,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
    else:
        await send_notification(from_user_id, f"{user_id} ha rechazado tu solicitud de partido para el {schedule} en {club}.")

    logger.info(f"Solicitud {request_id} respondida por {user_id}: {response}")
    return {"message": f"Solicitud {response} exitosamente"}

@router.get("/get_requests")
async def get_requests(user_id: str, db: firestore.Client = Depends(get_db)):
    """Obtiene las solicitudes de partido pendientes para un usuario."""
    if not user_id:
        raise HTTPException(status_code=400, detail="Falta user_id")

    requests = db.collection('match_requests').where(filter=FieldFilter('to_user_id', '==', user_id)).where(filter=FieldFilter('status', '==', 'pending')).get()
    pending_requests = []

    for req in requests:
        req_data = req.to_dict()
        pending_requests.append({
            'request_id': req.id,
            'from_user_id': req_data['from_user_id'],
            'club': req_data['club'],
            'schedule': req_data['schedule'],
            'timestamp': req_data.get('timestamp')
        })

    logger.info(f"Obtenidas {len(pending_requests)} solicitudes pendientes para {user_id}")
    return {"pending_requests": pending_requests}