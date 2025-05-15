from fastapi import APIRouter, HTTPException, Depends, status, Query, WebSocket, WebSocketDisconnect
from firebase_admin import firestore, messaging
from app.core.deps import get_current_user
from app.schemas.user import UserInDB
from app.schemas.notification import NotificationResponse, NotificationCreate
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging
from pydantic import BaseModel
from app.services.notifications import notification_service
import json
import asyncio

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Almacena las conexiones WebSocket activas
active_connections: Dict[str, List[WebSocket]] = {}

class PushNotification(BaseModel):
    """Modelo para notificaciones push."""
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    image: Optional[str] = None

def get_db():
    """Obtiene una instancia de la base de datos Firestore."""
    try:
        return firestore.client()
    except ValueError as e:
        logger.error(f"Error inicializando Firestore: {str(e)}")
        raise HTTPException(status_code=500, detail="Error inicializando Firestore")

@router.get("/", response_model=List[NotificationResponse], summary="Listar notificaciones", tags=["notifications"])
async def list_notifications(
    current_user: UserInDB = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False, description="Filtrar solo notificaciones no leídas")
):
    """
    Lista las notificaciones del usuario.
    
    Args:
        current_user: Usuario autenticado
        limit: Número máximo de notificaciones a retornar (1-100)
        offset: Número de notificaciones a saltar
        unread_only: Si es True, solo retorna notificaciones no leídas
        
    Returns:
        List[NotificationResponse]: Lista de notificaciones
    """
    try:
        db = get_db()
        query = db.collection("notifications").where("user_id", "==", current_user.id)
        
        if unread_only:
            query = query.where("read", "==", False)
            
        query = query.order_by("created_at", direction='DESCENDING')
        
        notifications = query.limit(limit).offset(offset).get()
        return [n.to_dict() for n in notifications]
        
    except Exception as e:
        logger.error(f"Error al listar notificaciones: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar notificaciones"
        )

@router.post("/{notification_id}/read", response_model=dict, summary="Marcar notificación como leída", tags=["notifications"])
async def mark_notification_read(
    notification_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Marca una notificación como leída.
    
    Args:
        notification_id: ID de la notificación
        current_user: Usuario autenticado
        
    Returns:
        dict: Mensaje de confirmación
    """
    try:
        notification_service.mark_as_read(notification_id)
        return {"message": "Notificación marcada como leída"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error al marcar notificación como leída: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al marcar notificación como leída")

@router.delete("/{notification_id}", response_model=dict, summary="Eliminar notificación", tags=["notifications"])
async def delete_notification(
    notification_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Elimina una notificación.
    
    Args:
        notification_id: ID de la notificación
        current_user: Usuario autenticado
        
    Returns:
        dict: Mensaje de confirmación
    """
    try:
        db = get_db()
        notif = db.collection("notifications").document(notification_id).get()
        
        if not notif.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notificación no encontrada"
            )
            
        notif_data = notif.to_dict()
        if notif_data.get("user_id") != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar esta notificación"
            )
            
        db.collection("notifications").document(notification_id).delete()
        return {"message": "Notificación eliminada"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar notificación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar notificación"
        )

@router.post("/send-push", response_model=dict, summary="Enviar notificación push", tags=["notifications"])
async def send_push_notification(
    user_id: str,
    notification: PushNotification,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Envía una notificación push a un usuario.
    
    Args:
        user_id: ID del usuario destinatario
        notification: Datos de la notificación push
        current_user: Usuario autenticado
        
    Returns:
        dict: Información de la notificación enviada
    """
    try:
        db = get_db()
        
        user_doc = db.collection("users").document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
            
        user_data = user_doc.to_dict()
        device_token = user_data.get("device_token")
        
        if not device_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario no tiene un token de dispositivo registrado"
            )
            
        message = messaging.Message(
            notification=messaging.Notification(
                title=notification.title,
                body=notification.body,
                image=notification.image
            ),
            data=notification.data or {},
            token=device_token
        )
        
        response = messaging.send(message)
        
        notification_id = str(uuid.uuid4())
        notification_data = {
            "notification_id": notification_id,
            "user_id": user_id,
            "type": "push",
            "title": notification.title,
            "body": notification.body,
            "data": notification.data,
            "image": notification.image,
            "created_at": datetime.now(),
            "read": False,
            "push_id": response
        }
        
        db.collection("notifications").document(notification_id).set(notification_data)
        
        return {
            "message": "Notificación push enviada",
            "notification_id": notification_id,
            "push_id": response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al enviar notificación push: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar notificación push"
        )

@router.post("/send-email", response_model=dict, summary="Enviar notificación por email", tags=["notifications"])
async def send_email_notification(
    user_id: str,
    subject: str = Query(..., description="Asunto del email"),
    body: str = Query(..., description="Contenido del email"),
    template: Optional[str] = Query(None, description="Plantilla de email a usar"),
    data: Optional[Dict] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Envía una notificación por email a un usuario.
    - Verifica que el usuario tenga un email válido.
    - Envía el email usando el servicio de email.
    - Guarda la notificación en la base de datos.
    """
    try:
        db = get_db()
        
        # Verificar usuario
        user_doc = db.collection("users").document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
            
        user_data = user_doc.to_dict()
        email = user_data.get("email")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario no tiene un email registrado"
            )
            
        # TODO: Implementar envío de email usando el servicio de email
        # Por ahora solo simulamos el envío
        
        # Guardar en base de datos
        notification_id = str(uuid.uuid4())
        notification_data = {
            "notification_id": notification_id,
            "user_id": user_id,
            "type": "email",
            "title": subject,
            "body": body,
            "template": template,
            "data": data,
            "created_at": datetime.now(),
            "read": False
        }
        
        db.collection("notifications").document(notification_id).set(notification_data)
        
        return {
            "message": "Notificación por email enviada",
            "notification_id": notification_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al enviar notificación por email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al enviar notificación por email"
        )

@router.get("/notifications", response_model=List[dict])
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Obtiene las notificaciones del usuario actual.
    
    Args:
        unread_only: Si es True, solo devuelve notificaciones no leídas
        limit: Número máximo de notificaciones a devolver
        current_user: Usuario actual (inyectado por FastAPI)
    """
    try:
        notifications = notification_service.get_user_notifications(
            user_id=current_user.id,
            limit=limit,
            unread_only=unread_only
        )
        return notifications
    except Exception as e:
        logger.error(f"Error al obtener notificaciones: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener notificaciones"
        )

@router.post("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Marca una notificación como leída.
    
    Args:
        notification_id: ID de la notificación
        current_user: Usuario actual (inyectado por FastAPI)
    """
    try:
        # Verificar que la notificación pertenece al usuario
        notifications = notification_service.get_user_notifications(
            user_id=current_user.id,
            limit=1,
            unread_only=True
        )
        
        if not any(n['id'] == notification_id for n in notifications):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notificación no encontrada o no tienes permiso para marcarla como leída"
            )
        
        notification_service.mark_as_read(notification_id)
        return {"message": "Notificación marcada como leída"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al marcar notificación como leída: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al marcar notificación como leída"
        )

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    Endpoint WebSocket para notificaciones en tiempo real.
    
    Args:
        websocket: Conexión WebSocket
        user_id: ID del usuario
    """
    await websocket.accept()
    
    if user_id not in active_connections:
        active_connections[user_id] = []
    active_connections[user_id].append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Procesar mensajes del cliente si es necesario
    except WebSocketDisconnect:
        active_connections[user_id].remove(websocket)
        if not active_connections[user_id]:
            del active_connections[user_id]
    except Exception as e:
        logger.error(f"Error en WebSocket: {str(e)}")
        if websocket in active_connections.get(user_id, []):
            active_connections[user_id].remove(websocket) 