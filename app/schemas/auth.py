from pydantic import BaseModel, EmailStr, Field, field_validator, constr
from typing import Optional
import re
from datetime import datetime, timezone

class Token(BaseModel):
    """Respuesta con token de acceso JWT."""
    access_token: str = Field(..., json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6..."})
    token_type: str = Field(..., json_schema_extra={"example": "bearer"})

class TokenRefreshRequest(BaseModel):
    """Petición para refrescar el token de acceso."""
    refresh_token: str = Field(..., json_schema_extra={"example": "refresh-token-uuid"})

class TokenRefreshResponse(BaseModel):
    """Respuesta con nuevo access token y refresh token."""
    access_token: str = Field(..., json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6..."})
    token_type: str = Field(..., json_schema_extra={"example": "bearer"})
    refresh_token: str = Field(..., json_schema_extra={"example": "refresh-token-uuid"})

class LogoutRequest(BaseModel):
    """Petición para cerrar sesión (invalidar refresh token)."""
    refresh_token: str = Field(..., json_schema_extra={"example": "refresh-token-uuid"})

class EmailVerificationRequest(BaseModel):
    """Petición para verificar email."""
    token: str = Field(..., json_schema_extra={"example": "verification-token-123"})

class ResendVerificationRequest(BaseModel):
    """Petición para reenviar email de verificación."""
    email: EmailStr = Field(..., json_schema_extra={"example": "testuser@example.com"})

class ForgotPasswordRequest(BaseModel):
    """Petición para solicitar recuperación de contraseña."""
    email: EmailStr = Field(..., json_schema_extra={"example": "testuser@example.com"})

class ResetPasswordRequest(BaseModel):
    """Petición para restablecer la contraseña usando un token de recuperación."""
    token: str = Field(..., json_schema_extra={"example": "reset-token-uuid"})
    new_password: str = Field(..., json_schema_extra={"example": "NewPass123"})

    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    username: str = Field(..., min_length=3, max_length=50)
    name: Optional[str] = None
    nivel: Optional[str] = None
    posicion_preferida: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenRefresh(BaseModel):
    refresh_token: str

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8)
    display_name: Optional[str] = None

class UserResponse(BaseModel):
    uid: str
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse 