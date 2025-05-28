from fastapi import APIRouter, HTTPException, status, Body, Depends, Request
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings
from app.services.auth_service import AuthService, validate_password
from app.services.email import email_service
from app.core.config.firebase import get_firebase_clients
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest, TokenResponse, UserResponse
from uuid import uuid4
import firebase_admin
from firebase_admin import auth as firebase_auth

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PreferencesOnboarding(BaseModel):
    nivel_juego: str = Field(..., description="Nivel de juego: principiante, intermedio, avanzado")
    lado_dominante: str = Field(..., description="Lado dominante: izquierda, derecha, ambas")
    estilo_juego: str = Field(None, description="Estilo de juego (opcional)")
    frecuencia_juego: int = Field(None, description="Frecuencia de juego semanal (opcional)")
    objetivos: str = Field(None, description="Objetivos del usuario (opcional)")

class ProfileOnboarding(BaseModel):
    edad: int = Field(None, description="Edad (opcional)")
    genero: str = Field(None, description="Género (opcional)")
    ubicacion: str = Field(None, description="Ubicación (opcional)")
    foto_perfil: str = Field(None, description="URL de la foto de perfil (opcional)")

@router.post("/register", response_model=TokenResponse, summary="Registro de usuario", tags=["auth"])
async def register_user(user_data: UserCreate):
    """
    Registra un nuevo usuario y lo autentica automáticamente.
    """
    user, error = await AuthService.register_user(user_data)
    if error:
        raise HTTPException(status_code=400, detail=error)
    # Login automático
    token_data, login_error = await AuthService.login_user(user_data.email, user_data.password)
    if login_error:
        raise HTTPException(status_code=400, detail=login_error)
    return token_data

@router.post("/login", response_model=TokenResponse, summary="Inicio de sesión", tags=["auth"])
async def login(user_data: UserLogin, request: Request):
    """
    Inicia sesión en el sistema usando Firebase Auth.
    """
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    token_data, login_error = await AuthService.login_user(user_data.email, user_data.password, ip, user_agent)
    if login_error:
        raise HTTPException(status_code=401, detail=login_error)
    return token_data

# --- Recuperación de contraseña: solicitar email ---
@router.post("/forgot-password", summary="Solicitar recuperación de contraseña", tags=["auth"])
async def forgot_password(request: ForgotPasswordRequest):
    clients = get_firebase_clients()
    db = clients['db']
    # Buscar usuario por email
    user_docs = db.collection('users').where('email', '==', request.email).get()
    if not user_docs:
        # No revelar si el email existe o no
        return {"message": "Si el email existe, se ha enviado un enlace de recuperación"}
    user_doc = user_docs[0]
    user_id = user_doc.id
    # Generar token único y expiración (1 hora)
    token = str(uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db.collection('password_reset_tokens').document(token).set({
        'user_id': user_id,
        'email': request.email,
        'expires_at': expires_at.isoformat()
    })
    # Enviar email (mock)
    email_service.send_password_reset_email(request.email, token)
    return {"message": "Si el email existe, se ha enviado un enlace de recuperación"}

# --- Recuperación de contraseña: restablecer ---
@router.post("/reset-password", summary="Restablecer contraseña", tags=["auth"])
async def reset_password(request: ResetPasswordRequest):
    clients = get_firebase_clients()
    db = clients['db']
    token_doc = db.collection('password_reset_tokens').document(request.token).get()
    if not token_doc.exists:
        raise HTTPException(status_code=400, detail="Token inválido o expirado")
    token_data = token_doc.to_dict()
    user_id = token_data['user_id']
    email = token_data['email']
    try:
        validate_password(request.new_password, email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Actualizar contraseña en Firebase Auth
    auth = clients['auth']
    auth.update_user(user_id, password=request.new_password)
    db.collection('password_reset_tokens').document(request.token).delete()
    return {"message": "Contraseña actualizada correctamente"}

# Helper para obtener el usuario actual desde el token
async def get_current_user(request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token de autenticación requerido")
    token = auth_header.split()[1]
    try:
        decoded = firebase_auth.verify_id_token(token)
        return decoded
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

@router.get("/sessions", summary="Listar sesiones activas", tags=["auth"])
async def list_sessions(request: Request, user=Depends(get_current_user)):
    clients = get_firebase_clients()
    db = clients['db']
    user_id = user['uid']
    sessions = db.collection('sessions').where('user_id', '==', user_id).where('is_active', '==', True).stream()
    result = []
    for s in sessions:
        data = s.to_dict()
        data['session_id'] = s.id
        result.append(data)
    return {"active_sessions": result}

@router.post("/logout-all", summary="Cerrar todas las sesiones", tags=["auth"])
async def logout_all(request: Request, user=Depends(get_current_user)):
    clients = get_firebase_clients()
    db = clients['db']
    user_id = user['uid']
    sessions = db.collection('sessions').where('user_id', '==', user_id).where('is_active', '==', True).stream()
    count = 0
    for s in sessions:
        db.collection('sessions').document(s.id).update({"is_active": False})
        count += 1
    return {"message": f"{count} sesiones cerradas correctamente"}

@router.post("/onboarding/preferences", summary="Onboarding: preferencias de juego", tags=["onboarding"])
async def onboarding_preferences(data: PreferencesOnboarding, user=Depends(get_current_user)):
    clients = get_firebase_clients()
    db = clients['db']
    user_id = user['uid']
    update_data = data.dict(exclude_unset=True)
    db.collection('users').document(user_id).update(update_data)
    return {"message": "Preferencias guardadas correctamente"}

@router.post("/onboarding/profile", summary="Onboarding: configuración inicial", tags=["onboarding"])
async def onboarding_profile(data: ProfileOnboarding, user=Depends(get_current_user)):
    clients = get_firebase_clients()
    db = clients['db']
    user_id = user['uid']
    update_data = data.dict(exclude_unset=True)
    db.collection('users').document(user_id).update(update_data)
    return {"message": "Perfil actualizado correctamente"}

async def require_onboarding_completed(user=Depends(get_current_user)):
    clients = get_firebase_clients()
    db = clients['db']
    user_id = user['uid']
    user_doc = db.collection('users').document(user_id).get()
    if not user_doc.exists:
        raise HTTPException(status_code=403, detail="Usuario no encontrado")
    data = user_doc.to_dict()
    if not data.get('nivel_juego') or not data.get('lado_dominante') or not data.get('video_inicial_subido'):
        raise HTTPException(
            status_code=403,
            detail="Debes completar tu onboarding (nivel de juego, lado dominante y subir tu video inicial) para acceder a esta función."
        )
    return user

# Ejemplo de uso en un endpoint protegido
@router.get("/protected/sessions", summary="Listar sesiones activas (requiere onboarding)", tags=["auth"])
async def list_sessions_protected(request: Request, user=Depends(require_onboarding_completed)):
    clients = get_firebase_clients()
    db = clients['db']
    user_id = user['uid']
    sessions = db.collection('sessions').where('user_id', '==', user_id).where('is_active', '==', True).stream()
    result = []
    for s in sessions:
        data = s.to_dict()
        data['session_id'] = s.id
        result.append(data)
    return {"active_sessions": result} 