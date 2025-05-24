from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.auth import UserCreate, UserResponse, TokenResponse, UserLogin
from app.services.auth_service import AuthService
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """
    Registra un nuevo usuario.
    """
    user, error = await AuthService.register_user(user_data)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return user

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """
    Autentica un usuario y retorna un token.
    """
    token_data, error = await AuthService.login_user(login_data.email, login_data.password)
    if error:
        raise HTTPException(status_code=401, detail=error)
    return token_data

@router.get("/me", response_model=UserResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Obtiene la información del usuario actual.
    """
    user, error = await AuthService.get_current_user(credentials.credentials)
    if error:
        raise HTTPException(status_code=401, detail=error)
    return user 