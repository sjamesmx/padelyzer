from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class MatchStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class MatchRequest(BaseModel):
    location: str
    date: datetime
    time: str
    duration: int  # en minutos
    level: str
    position: str
    notes: Optional[str] = None

class MatchResponse(MatchRequest):
    id: str
    user_id: str
    status: MatchStatus
    created_at: datetime
    updated_at: datetime
    accepted_by: Optional[str] = None
    rejected_by: Optional[str] = None 