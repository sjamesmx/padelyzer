from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime

class UserPreferences(BaseModel):
    notifications: bool = True
    email_notifications: bool = True
    language: str = "es"
    timezone: str = "UTC"

class UserStats(BaseModel):
    matches_played: int = 0
    matches_won: int = 0
    total_points: int = 0

class UserLocation(BaseModel):
    latitude: float
    longitude: float

class UserBase(BaseModel):
    email: EmailStr
    name: str
    nivel: str
    posicion_preferida: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    nivel: Optional[str] = None
    posicion_preferida: Optional[str] = None
    preferences: Optional[UserPreferences] = None
    clubs: Optional[List[str]] = None
    availability: Optional[List[str]] = None
    location: Optional[UserLocation] = None

class UserInDB(UserBase):
    id: str
    email_verified: bool = False
    is_active: bool = True
    fecha_registro: datetime
    ultimo_analisis: Optional[str] = None
    tipo_ultimo_analisis: Optional[str] = None
    fecha_ultimo_analisis: Optional[datetime] = None
    preferences: UserPreferences = UserPreferences()
    stats: UserStats = UserStats()
    achievements: List[str] = []
    blocked_users: List[str] = []
    padel_iq: Optional[float] = None
    clubs: List[str] = []
    availability: List[str] = []
    location: Optional[UserLocation] = None
    onboarding_status: str = "pending"
    last_login: Optional[datetime] = None
    verification_token: Optional[str] = None

class User(UserInDB):
    pass

class UserResponseSchema(UserInDB):
    pass

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class PrivacySettings(BaseModel):
    profile_visible: bool = True
    show_email: bool = False
    show_stats: bool = True

class Preferences(BaseModel):
    posicion_preferida: Optional[str] = None
    notificaciones: Optional[bool] = True
    idioma: Optional[str] = "es"

class PrivacyUpdateRequest(BaseModel):
    privacy: PrivacySettings

class PreferencesUpdateRequest(BaseModel):
    preferences: Preferences

class DeleteAccountRequest(BaseModel):
    password: str 