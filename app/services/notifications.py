from firebase_admin import firestore
from datetime import datetime
import uuid
import logging
from typing import Optional, List, Dict, Any, Callable
from app.core.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self._db = None
        self._collection = None
        self.max_notifications = 100  # Límite máximo de notificaciones por usuario
        self._listeners: Dict[str, List[Callable]] = {}  # Almacena los listeners activos

    @property
    def db(self):
        if self._db is None:
            self._db = firestore.client()
        return self._db

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.db.collection('notifications')
        return self._collection

    def create_notification(self, user_id: str, type: str, title: str, message: str, data: Optional[Dict[str, Any]] = None) -> str:
        """
        Crea una nueva notificación en Firestore y notifica a los listeners.
        
        Args:
            user_id: ID del usuario que recibirá la notificación
            type: Tipo de notificación (ej: 'analysis_completed', 'match_invitation')
            title: Título de la notificación
            message: Mensaje de la notificación
            data: Datos adicionales relacionados con la notificación
            
        Returns:
            str: ID de la notificación creada
            
        Raises:
            ValueError: Si los parámetros requeridos son inválidos
            Exception: Si ocurre un error al crear la notificación
        """
        try:
            # Validar parámetros requeridos
            if not all([user_id, type, title, message]):
                raise ValueError("Todos los campos son requeridos: user_id, type, title, message")
                
            # Validar tipo de notificación
            if type not in settings.NOTIFICATION_TYPES:
                raise ValueError(f"Tipo de notificación inválido: {type}")
            
            notification_id = str(uuid.uuid4())
            notification_data = {
                'id': notification_id,
                'user_id': user_id,
                'type': type,
                'title': title,
                'message': message,
                'data': data or {},
                'read': False,
                'created_at': datetime.utcnow()
            }
            
            # Crear notificación en Firestore
            self.collection.document(notification_id).set(notification_data)
            logger.info(f"Notificación creada: {notification_id} para usuario {user_id}")
            
            # Notificar a los listeners
            self._notify_listeners(user_id, notification_data)
            
            # Limpiar notificaciones antiguas si excede el límite
            self._cleanup_old_notifications(user_id)
            
            return notification_id
            
        except Exception as e:
            logger.error(f"Error al crear notificación: {str(e)}")
            raise

    def mark_as_read(self, notification_id: str) -> None:
        """
        Marca una notificación como leída y notifica a los listeners.
        
        Args:
            notification_id: ID de la notificación a marcar como leída
            
        Raises:
            ValueError: Si el ID de la notificación es inválido
            Exception: Si ocurre un error al marcar la notificación como leída
        """
        try:
            if not notification_id:
                raise ValueError("ID de notificación requerido")
            
            # Obtener la notificación actual
            notification_ref = self.collection.document(notification_id)
            notification = notification_ref.get()
            
            if not notification.exists:
                raise ValueError(f"Notificación no encontrada: {notification_id}")
            
            notification_data = notification.to_dict()
            user_id = notification_data.get('user_id')
            
            # Actualizar estado
            notification_ref.update({
                'read': True,
                'read_at': datetime.utcnow()
            })
            logger.info(f"Notificación marcada como leída: {notification_id}")
            
            # Notificar a los listeners
            if user_id:
                self._notify_listeners(user_id, {**notification_data, 'read': True})
                
        except Exception as e:
            logger.error(f"Error al marcar notificación como leída: {str(e)}")
            raise

    def get_user_notifications(self, user_id: str, limit: int = 50, unread_only: bool = False) -> List[Dict[str, Any]]:
        """
        Obtiene las notificaciones de un usuario.
        
        Args:
            user_id: ID del usuario
            limit: Límite de notificaciones a obtener (máximo 100)
            unread_only: Si es True, solo devuelve notificaciones no leídas
            
        Returns:
            List[Dict[str, Any]]: Lista de notificaciones
            
        Raises:
            ValueError: Si el ID de usuario es inválido
            Exception: Si ocurre un error al obtener las notificaciones
        """
        try:
            if not user_id:
                raise ValueError("ID de usuario requerido")
                
            # Asegurar que el límite no exceda el máximo permitido
            limit = min(limit, self.max_notifications)
            
            query = self.collection.where('user_id', '==', user_id)
            if unread_only:
                query = query.where('read', '==', False)
            
            notifications = query.order_by('created_at', direction='DESCENDING').limit(limit).get()
            return [doc.to_dict() for doc in notifications]
        except Exception as e:
            logger.error(f"Error al obtener notificaciones: {str(e)}")
            raise

    def subscribe_to_notifications(self, user_id: str, callback: Callable[[Dict[str, Any]], None]) -> str:
        """
        Suscribe un callback para recibir notificaciones en tiempo real.
        
        Args:
            user_id: ID del usuario
            callback: Función a llamar cuando haya cambios en las notificaciones
            
        Returns:
            str: ID de la suscripción
        """
        try:
            if not user_id or not callback:
                raise ValueError("user_id y callback son requeridos")
            
            subscription_id = str(uuid.uuid4())
            
            # Almacenar el callback
            if user_id not in self._listeners:
                self._listeners[user_id] = []
            self._listeners[user_id].append(callback)
            
            logger.info(f"Nueva suscripción creada: {subscription_id} para usuario {user_id}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"Error al crear suscripción: {str(e)}")
            raise

    def unsubscribe_from_notifications(self, user_id: str, subscription_id: str) -> None:
        """
        Cancela una suscripción a notificaciones.
        
        Args:
            user_id: ID del usuario
            subscription_id: ID de la suscripción a cancelar
        """
        try:
            if user_id in self._listeners:
                self._listeners[user_id] = [
                    callback for callback in self._listeners[user_id]
                    if id(callback) != subscription_id
                ]
                logger.info(f"Suscripción cancelada: {subscription_id} para usuario {user_id}")
        except Exception as e:
            logger.error(f"Error al cancelar suscripción: {str(e)}")
            raise

    def _notify_listeners(self, user_id: str, notification_data: Dict[str, Any]) -> None:
        """
        Notifica a todos los listeners registrados para un usuario.
        
        Args:
            user_id: ID del usuario
            notification_data: Datos de la notificación
        """
        try:
            if user_id in self._listeners:
                for callback in self._listeners[user_id]:
                    try:
                        callback(notification_data)
                    except Exception as e:
                        logger.error(f"Error al notificar listener: {str(e)}")
        except Exception as e:
            logger.error(f"Error al notificar listeners: {str(e)}")

    def _cleanup_old_notifications(self, user_id: str) -> None:
        """
        Limpia notificaciones antiguas si el usuario excede el límite máximo.
        
        Args:
            user_id: ID del usuario
        """
        try:
            # Obtener todas las notificaciones del usuario ordenadas por fecha
            query = self.collection.where('user_id', '==', user_id)
            notifications = query.order_by('created_at', direction='DESCENDING').get()
            
            # Si excede el límite, eliminar las más antiguas
            if len(notifications) > self.max_notifications:
                for doc in notifications[self.max_notifications:]:
                    doc.reference.delete()
                logger.info(f"Notificaciones antiguas eliminadas para usuario {user_id}")
        except Exception as e:
            logger.error(f"Error al limpiar notificaciones antiguas: {str(e)}")

# Instancia global del servicio de notificaciones
notification_service = NotificationService() 