from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class Token(BaseModel):
    """Respuesta con token de acceso JWT."""
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6...")
    token_type: str = Field(..., example="bearer")

class TokenRefreshRequest(BaseModel):
    """Petición para refrescar el token de acceso."""
    refresh_token: str = Field(..., example="refresh-token-uuid")

class TokenRefreshResponse(BaseModel):
    """Respuesta con nuevo access token y refresh token."""
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6...")
    token_type: str = Field(..., example="bearer")
    refresh_token: str = Field(..., example="refresh-token-uuid")

class LogoutRequest(BaseModel):
    """Petición para cerrar sesión (invalidar refresh token)."""
    refresh_token: str = Field(..., example="refresh-token-uuid")

class EmailVerificationRequest(BaseModel):
    """Petición para verificar email."""
    token: str = Field(..., example="verification-token-123")

class ResendVerificationRequest(BaseModel):
    """Petición para reenviar email de verificación."""
    email: EmailStr = Field(..., example="testuser@example.com")

class ForgotPasswordRequest(BaseModel):
    """Petición para solicitar recuperación de contraseña."""
    email: EmailStr = Field(..., example="testuser@example.com")

class ResetPasswordRequest(BaseModel):
    """Petición para restablecer la contraseña usando un token de recuperación."""
    token: str = Field(..., example="reset-token-uuid")
    new_password: str = Field(..., example="NewPass123") 