from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from firebase_admin import auth, credentials, initialize_app

from app.core.config import settings
from app.core.exceptions import PadelException
from app.schemas.token import TokenPayload
from app.services.firebase.firebase_config import get_firebase_app

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependencia para obtener el usuario actual basado en el token JWT
    """
    try:
        # Verificar token con Firebase
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise PadelException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Error al validar credenciales",
            error_type="AUTH_ERROR"
        )

def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Dependencia para verificar que el usuario está activo
    """
    if not current_user.get("email_verified", False):
        raise PadelException(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Usuario no verificado",
            error_type="AUTH_ERROR"
        )
    return current_user

def get_firebase_auth() -> Generator:
    """
    Dependencia para obtener el cliente de autenticación de Firebase
    """
    try:
        app = get_firebase_app()
        yield auth.Client(app)
    except Exception as e:
        raise PadelException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al inicializar Firebase Auth",
            error_type="FIREBASE_ERROR"
        ) 