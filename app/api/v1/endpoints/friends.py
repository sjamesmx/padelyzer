from fastapi import APIRouter, HTTPException, Depends, status, Query
from firebase_admin import firestore
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
from typing import List, Optional
import uuid
from datetime import datetime
import logging
from app.schemas.friends import (
    FriendshipRequest, Friendship, BlockedUser, BlockUserRequest, BlockedUserList
)
from app.services.firebase import get_firebase_client
from app.services.notifications import notification_service

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def get_db():
    """Obtiene la instancia de Firestore."""
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

async def check_blocked(blocker_id: str, blocked_id: str) -> bool:
    """Verifica si un usuario está bloqueado por otro."""
    db = get_firebase_client()
    blocks_ref = db.collection('blocked_users')
    query = blocks_ref.where('blocker_id', '==', blocker_id).where('blocked_id', '==', blocked_id)
    results = query.get()
    return len(results) > 0

@router.post("/request/{target_user_id}", response_model=FriendshipRequest, summary="Enviar solicitud de amistad", tags=["friends"])
async def send_friend_request(
    target_user_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Envía una solicitud de amistad a otro usuario.
    - Verifica que el usuario no esté bloqueado.
    - Crea una notificación para el usuario objetivo.
    """
    try:
        # Verificar si el usuario está bloqueado
        if await check_blocked(target_user_id, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes enviar solicitudes a este usuario"
            )

        db = get_firebase_client()
        
        # Verificar si ya existe una solicitud
        requests_ref = db.collection('friendship_requests')
        query = requests_ref.where('sender_id', '==', current_user.id).where('receiver_id', '==', target_user_id)
        results = query.get()
        
        if results:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya has enviado una solicitud a este usuario"
            )
        
        # Crear solicitud
        request_id = str(uuid.uuid4())
        request_data = {
            'sender_id': current_user.id,
            'receiver_id': target_user_id,
            'status': 'pending',
            'created_at': datetime.now()
        }
        requests_ref.document(request_id).set(request_data)
        
        # Crear notificación
        notification_service.create_notification(
            user_id=target_user_id,
            type="friend_request",
            title="Nueva solicitud de amistad",
            message=f"{current_user.name} te ha enviado una solicitud de amistad",
            data={"request_id": request_id}
        )
        
        return {**request_data, 'id': request_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al enviar solicitud de amistad: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar solicitud de amistad"
        )

@router.post("/accept/{request_id}", response_model=Friendship, summary="Aceptar solicitud de amistad", tags=["friends"])
async def accept_friend_request(
    request_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Acepta una solicitud de amistad.
    - Crea la relación de amistad.
    - Notifica al remitente.
    """
    try:
        db = get_firebase_client()
        
        # Obtener solicitud
        request_doc = db.collection('friendship_requests').document(request_id).get()
        if not request_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada"
            )
            
        request_data = request_doc.to_dict()
        if request_data['receiver_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para aceptar esta solicitud"
            )
            
        if request_data['status'] != 'pending':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La solicitud ya no está pendiente"
            )
            
        # Crear amistad
        friendship_id = str(uuid.uuid4())
        friendship_data = {
            'user1_id': request_data['sender_id'],
            'user2_id': current_user.id,
            'created_at': datetime.now()
        }
        db.collection('friendships').document(friendship_id).set(friendship_data)
        
        # Actualizar estado de la solicitud
        request_doc.reference.update({'status': 'accepted'})
        
        # Notificar al remitente
        notification_service.create_notification(
            user_id=request_data['sender_id'],
            type="friend_request_accepted",
            title="Solicitud de amistad aceptada",
            message=f"{current_user.name} ha aceptado tu solicitud de amistad",
            data={"friendship_id": friendship_id}
        )
        
        return {**friendship_data, 'id': friendship_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al aceptar solicitud de amistad: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al aceptar solicitud de amistad"
        )

@router.post("/reject/{request_id}", response_model=FriendshipRequest, summary="Rechazar solicitud de amistad", tags=["friends"])
async def reject_friend_request(
    request_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Rechaza una solicitud de amistad.
    - Actualiza el estado de la solicitud.
    - Notifica al remitente.
    """
    try:
        db = get_firebase_client()
        
        # Obtener solicitud
        request_doc = db.collection('friendship_requests').document(request_id).get()
        if not request_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada"
            )
            
        request_data = request_doc.to_dict()
        if request_data['receiver_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para rechazar esta solicitud"
            )
            
        if request_data['status'] != 'pending':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La solicitud ya no está pendiente"
            )
            
        # Actualizar estado de la solicitud
        request_doc.reference.update({
            'status': 'rejected',
            'rejected_at': datetime.now()
        })
        
        # Notificar al remitente
        notification_service.create_notification(
            user_id=request_data['sender_id'],
            type="friend_request_rejected",
            title="Solicitud de amistad rechazada",
            message=f"{current_user.name} ha rechazado tu solicitud de amistad",
            data={"request_id": request_id}
        )
        
        return {**request_data, 'id': request_id, 'status': 'rejected'}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al rechazar solicitud de amistad: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al rechazar solicitud de amistad"
        )

@router.get("/list", response_model=List[Friendship], summary="Listar amigos", tags=["friends"])
async def get_friends_list(
    current_user: UserInDB = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100, description="Número máximo de amigos a retornar"),
    offset: int = Query(0, ge=0, description="Número de amigos a saltar"),
    search: Optional[str] = Query(None, description="Buscar amigos por nombre")
):
    """
    Obtiene la lista de amigos del usuario.
    - Incluye información básica de cada amigo.
    - Soporta paginación y búsqueda.
    """
    try:
        db = get_firebase_client()
        
        # Obtener amistades donde el usuario es user1 o user2
        friendships_ref = db.collection('friendships')
        query1 = friendships_ref.where('user1_id', '==', current_user.id)
        query2 = friendships_ref.where('user2_id', '==', current_user.id)
        
        # Ejecutar queries
        results1 = query1.get()
        results2 = query2.get()
        
        # Combinar resultados
        friendships = []
        for doc in results1:
            data = doc.to_dict()
            data['id'] = doc.id
            data['friend_id'] = data['user2_id']
            friendships.append(data)
            
        for doc in results2:
            data = doc.to_dict()
            data['id'] = doc.id
            data['friend_id'] = data['user1_id']
            friendships.append(data)
            
        # Obtener información de los amigos
        friend_ids = [f['friend_id'] for f in friendships]
        users_ref = db.collection('users')
        users = {doc.id: doc.to_dict() for doc in users_ref.where('id', 'in', friend_ids).get()}
        
        # Enriquecer datos de amistad con información del usuario
        enriched_friendships = []
        for friendship in friendships:
            friend_data = users.get(friendship['friend_id'], {})
            if search and search.lower() not in friend_data.get('name', '').lower():
                continue
                
            enriched_friendship = {
                'id': friendship['id'],
                'friend': {
                    'id': friend_data.get('id'),
                    'name': friend_data.get('name'),
                    'level': friend_data.get('level'),
                    'preferred_position': friend_data.get('preferred_position'),
                    'profile_picture': friend_data.get('profile_picture')
                },
                'created_at': friendship['created_at']
            }
            enriched_friendships.append(enriched_friendship)
            
        # Ordenar por nombre
        enriched_friendships.sort(key=lambda x: x['friend']['name'])
        
        # Aplicar paginación
        total = len(enriched_friendships)
        paginated_friendships = enriched_friendships[offset:offset + limit]
        
        return {
            'friends': paginated_friendships,
            'total': total,
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        logger.error(f"Error al obtener lista de amigos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener lista de amigos"
        )

@router.get("/pending", response_model=List[FriendshipRequest], summary="Listar solicitudes pendientes", tags=["friends"])
async def get_pending_requests(
    current_user: UserInDB = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100, description="Número máximo de solicitudes a retornar"),
    offset: int = Query(0, ge=0, description="Número de solicitudes a saltar")
):
    """
    Obtiene la lista de solicitudes de amistad pendientes.
    - Incluye información del remitente.
    - Soporta paginación.
    """
    try:
        db = get_firebase_client()
        
        # Obtener solicitudes pendientes
        requests_ref = db.collection('friendship_requests')
        query = requests_ref.where('receiver_id', '==', current_user.id).where('status', '==', 'pending')
        
        # Ejecutar query
        results = query.get()
        
        # Procesar resultados
        requests = []
        for doc in results:
            data = doc.to_dict()
            data['id'] = doc.id
            requests.append(data)
            
        # Obtener información de los remitentes
        sender_ids = [r['sender_id'] for r in requests]
        users_ref = db.collection('users')
        users = {doc.id: doc.to_dict() for doc in users_ref.where('id', 'in', sender_ids).get()}
        
        # Enriquecer datos de solicitud con información del remitente
        enriched_requests = []
        for request in requests:
            sender_data = users.get(request['sender_id'], {})
            enriched_request = {
                'id': request['id'],
                'sender': {
                    'id': sender_data.get('id'),
                    'name': sender_data.get('name'),
                    'level': sender_data.get('level'),
                    'preferred_position': sender_data.get('preferred_position'),
                    'profile_picture': sender_data.get('profile_picture')
                },
                'status': request['status'],
                'created_at': request['created_at']
            }
            enriched_requests.append(enriched_request)
            
        # Ordenar por fecha de creación (más recientes primero)
        enriched_requests.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Aplicar paginación
        total = len(enriched_requests)
        paginated_requests = enriched_requests[offset:offset + limit]
        
        return {
            'requests': paginated_requests,
            'total': total,
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        logger.error(f"Error al obtener solicitudes pendientes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener solicitudes pendientes"
        )

@router.delete("/{friendship_id}", response_model=dict, summary="Eliminar amistad", tags=["friends"])
async def delete_friendship(
    friendship_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Elimina una relación de amistad.
    - Elimina la amistad de la base de datos.
    - Notifica al otro usuario.
    - Limpia datos relacionados.
    """
    try:
        db = get_firebase_client()
        
        # Obtener amistad
        friendship_doc = db.collection('friendships').document(friendship_id).get()
        if not friendship_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Amistad no encontrada"
            )
            
        friendship_data = friendship_doc.to_dict()
        
        # Verificar que el usuario es parte de la amistad
        if current_user.id not in [friendship_data['user1_id'], friendship_data['user2_id']]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar esta amistad"
            )
            
        # Obtener ID del otro usuario
        other_user_id = (
            friendship_data['user2_id']
            if friendship_data['user1_id'] == current_user.id
            else friendship_data['user1_id']
        )
        
        # Eliminar amistad
        friendship_doc.reference.delete()
        
        # Notificar al otro usuario
        notification_service.create_notification(
            user_id=other_user_id,
            type="friendship_deleted",
            title="Amistad eliminada",
            message=f"{current_user.name} ha eliminado la amistad contigo",
            data={"friendship_id": friendship_id}
        )
        
        # Limpiar datos relacionados
        # 1. Eliminar solicitudes pendientes entre los usuarios
        requests_ref = db.collection('friendship_requests')
        requests = requests_ref.where('sender_id', 'in', [current_user.id, other_user_id]).where(
            'receiver_id', 'in', [current_user.id, other_user_id]
        ).get()
        
        for request in requests:
            request.reference.delete()
            
        # 2. Eliminar bloqueos mutuos (opcional, depende de la lógica de negocio)
        blocks_ref = db.collection('blocked_users')
        blocks = blocks_ref.where('blocker_id', 'in', [current_user.id, other_user_id]).where(
            'blocked_id', 'in', [current_user.id, other_user_id]
        ).get()
        
        for block in blocks:
            block.reference.delete()
            
        return {
            "message": "Amistad eliminada correctamente",
            "friendship_id": friendship_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar amistad: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar amistad"
        )

@router.post("/block/{user_id}", response_model=BlockedUser, summary="Bloquear usuario", tags=["friends"])
async def block_user(
    user_id: str,
    request: BlockUserRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Bloquea a un usuario.
    - Elimina cualquier amistad existente.
    - Elimina cualquier solicitud pendiente.
    """
    try:
        db = get_firebase_client()
        
        # Verificar si ya está bloqueado
        if await check_blocked(current_user.id, user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario ya bloqueado"
            )
            
        # Crear bloqueo
        block_id = str(uuid.uuid4())
        block_data = {
            'blocker_id': current_user.id,
            'blocked_id': user_id,
            'reason': request.reason,
            'created_at': datetime.now()
        }
        db.collection('blocked_users').document(block_id).set(block_data)
        
        # Eliminar amistad si existe
        friendships_ref = db.collection('friendships')
        query = friendships_ref.where('user1_id', 'in', [current_user.id, user_id]).where('user2_id', 'in', [current_user.id, user_id])
        results = query.get()
        for doc in results:
            doc.reference.delete()
        
        # Eliminar solicitudes pendientes
        requests_ref = db.collection('friendship_requests')
        query = requests_ref.where('sender_id', 'in', [current_user.id, user_id]).where('receiver_id', 'in', [current_user.id, user_id])
        results = query.get()
        for doc in results:
            doc.reference.delete()
        
        return {**block_data, 'id': block_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al bloquear usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al bloquear usuario"
        )

@router.get("/blocked", response_model=BlockedUserList, summary="Listar usuarios bloqueados", tags=["friends"])
async def list_blocked_users(current_user: UserInDB = Depends(get_current_user)):
    """
    Lista los usuarios bloqueados por el usuario actual.
    """
    try:
        db = get_firebase_client()
        blocks_ref = db.collection('blocked_users')
        query = blocks_ref.where('blocker_id', '==', current_user.id)
        results = query.get()
        
        blocked_users = []
        for doc in results:
            block_data = doc.to_dict()
            blocked_users.append({**block_data, 'id': doc.id})
        
        return {"blocked_users": blocked_users}
        
    except Exception as e:
        logger.error(f"Error al listar usuarios bloqueados: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar usuarios bloqueados"
        )

@router.delete("/block/{user_id}", summary="Desbloquear usuario", tags=["friends"])
async def unblock_user(
    user_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Desbloquea a un usuario.
    """
    try:
        db = get_firebase_client()
        blocks_ref = db.collection('blocked_users')
        query = blocks_ref.where('blocker_id', '==', current_user.id).where('blocked_id', '==', user_id)
        results = query.get()
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no bloqueado"
            )
            
        results[0].reference.delete()
        return {"detail": "Usuario desbloqueado correctamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al desbloquear usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al desbloquear usuario"
        ) 