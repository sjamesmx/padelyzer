from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

class MatchStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class MatchRequest(BaseModel):
    to_user_id: str
    message: Optional[str] = Field(None, max_length=500)
    preferred_date: Optional[datetime]
    preferred_location: Optional[str] = Field(None, max_length=200)
    
    @validator('message')
    def message_not_empty_if_provided(cls, v):
        if v is not None and not v.strip():
            raise ValueError('El mensaje no puede estar vacío si se proporciona')
        return v

class MatchResponse(BaseModel):
    id: str
    from_user_id: str
    to_user_id: str
    status: MatchStatus
    message: Optional[str]
    preferred_date: Optional[datetime]
    preferred_location: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

class MatchRequestResponse(BaseModel):
    request_id: str
    status: MatchStatus
    message: Optional[str]

class MatchSearch(BaseModel):
    location: Optional[str] = Field(None, max_length=200)
    date: Optional[datetime]
    skill_level: Optional[str] = Field(None, pattern='^(beginner|intermediate|advanced|expert)$')
    max_distance: Optional[int] = Field(None, ge=1, le=100)
    
    @validator('max_distance')
    def validate_distance(cls, v):
        if v is not None and (v < 1 or v > 100):
            raise ValueError('La distancia máxima debe estar entre 1 y 100 km')
        return v

class MatchRating(BaseModel):
    match_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)
    
    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('La calificación debe estar entre 1 y 5')
        return v 