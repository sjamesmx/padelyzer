from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class NotificationBase(BaseModel):
    """Esquema base para notificaciones."""
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None

class NotificationCreate(NotificationBase):
    """Esquema para crear una notificación."""
    user_id: str

class NotificationResponse(NotificationBase):
    """Esquema para la respuesta de notificación."""
    id: str
    user_id: str
    read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True 