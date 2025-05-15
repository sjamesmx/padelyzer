from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class FriendshipRequest(BaseModel):
    """Solicitud de amistad."""
    id: str = Field(..., example="friendship-request-uuid")
    sender_id: str = Field(..., example="user-uuid")
    receiver_id: str = Field(..., example="user-uuid")
    status: str = Field(..., example="pending")
    created_at: datetime = Field(..., example="2024-05-11T13:24:53.473Z")

class Friendship(BaseModel):
    """Relación de amistad."""
    id: str = Field(..., example="friendship-uuid")
    user1_id: str = Field(..., example="user-uuid")
    user2_id: str = Field(..., example="user-uuid")
    created_at: datetime = Field(..., example="2024-05-11T13:24:53.473Z")

class BlockedUser(BaseModel):
    """Usuario bloqueado."""
    id: str = Field(..., example="block-uuid")
    blocker_id: str = Field(..., example="user-uuid")
    blocked_id: str = Field(..., example="user-uuid")
    created_at: datetime = Field(..., example="2024-05-11T13:24:53.473Z")
    reason: Optional[str] = Field(None, example="Comportamiento inapropiado")

class BlockUserRequest(BaseModel):
    """Petición para bloquear usuario."""
    reason: Optional[str] = Field(None, example="Comportamiento inapropiado")

class BlockedUserList(BaseModel):
    """Lista de usuarios bloqueados."""
    blocked_users: List[BlockedUser] = Field(..., example=[]) 