"""
Modelo de datos para la gestión de clubes de pádel.
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

class ClubBase(BaseModel):
    """Modelo base para los clubes."""
    name: str = Field(..., description="Nombre del club")
    description: Optional[str] = Field(None, description="Descripción del club")
    address: str = Field(..., description="Dirección del club")
    phone: str = Field(..., description="Teléfono de contacto")
    email: EmailStr = Field(..., description="Email de contacto")
    website: Optional[str] = Field(None, description="Sitio web del club")
    logo_url: Optional[str] = Field(None, description="URL del logo del club")
    active: bool = Field(default=True, description="Estado del club")

class ClubCreate(ClubBase):
    """Modelo para crear un nuevo club."""
    pass

class ClubUpdate(BaseModel):
    """Modelo para actualizar un club existente."""
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    active: Optional[bool] = None

class ClubInDB(ClubBase):
    """Modelo para representar un club en la base de datos."""
    id: str = Field(..., description="ID único del club")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    owner_id: str = Field(..., description="ID del propietario del club")
    member_count: int = Field(default=0, description="Número de miembros del club")

class Club(ClubInDB):
    """Modelo para representar un club en las respuestas de la API."""
    class Config:
        from_attributes = True 