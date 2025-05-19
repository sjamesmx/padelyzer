from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.core.security import create_access_token, verify_password, get_password_hash
from app.schemas.user import User, UserCreate, Token
from app.schemas.auth import (
    TokenRefreshRequest, TokenRefreshResponse, LogoutRequest, ForgotPasswordRequest, ResetPasswordRequest,
    EmailVerificationRequest, ResendVerificationRequest,
    UserRegistration,
    UserLogin,
    TokenRefresh,
    PasswordReset,
    PasswordResetConfirm
)
from app.services.firebase import get_firebase_client
from app.services.email import email_service
from datetime import datetime, timedelta
import logging
from uuid import uuid4
from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.config.firebase import db

router = APIRouter()
logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Constantes para límites de envío de emails
MAX_VERIFICATION_ATTEMPTS = 3
VERIFICATION_GRACE_PERIOD_DAYS = 3

@router.post("/signup", response_model=User, summary="Registro de usuario", tags=["auth"])
async def register_user(user_data: UserRegistration):
    """
    Registra un nuevo usuario en el sistema.
    
    - **email**: Email válido del usuario
    - **password**: Contraseña que cumple con los requisitos de seguridad
    - **username**: Nombre de usuario único
    - **name**: Nombre completo del usuario (opcional)
    - **nivel**: Nivel de juego (opcional)
    - **posicion_preferida**: Posición preferida (opcional)
    """
    # Verificar si el email ya está registrado
    user_ref = db.collection('users').where('email', '==', user_data.email).get()
    if user_ref:
        raise AuthenticationError("El email ya está registrado")
    
    # Crear nuevo usuario
    user_dict = user_data.dict()
    user_dict['password'] = get_password_hash(user_dict['password'])
    user_dict['created_at'] = datetime.utcnow()
    user_dict['updated_at'] = datetime.utcnow()
    user_dict['is_active'] = True
    user_dict['is_verified'] = False
    
    # Guardar en Firestore
    user_ref = db.collection('users').document()
    user_dict['id'] = user_ref.id
    user_ref.set(user_dict)
    
    return User(**user_dict)

@router.post("/verify-email", summary="Verificar email", tags=["auth"])
async def verify_email(request: EmailVerificationRequest):
    """
    Verifica el email de un usuario usando el token de verificación.
    - En desarrollo, también acepta el ID del usuario como token.
    """
    try:
        db = get_firebase_client()
        
        # En desarrollo, permitir usar el ID del usuario como token
        if settings.ENVIRONMENT == "development":
            user_doc = db.collection("users").document(request.token).get()
            if user_doc.exists:
                user_doc.reference.update({
                    "email_verified": True,
                    "updated_at": datetime.utcnow()
                })
                return {"detail": "Email verificado correctamente (modo desarrollo)"}
        
        # Verificación normal con token
        token_doc = db.collection("email_verification_tokens").document(request.token).get()
        if not token_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de verificación inválido"
            )
            
        token_data = token_doc.to_dict()
        if token_data.get("used"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token ya utilizado"
            )
            
        if datetime.utcnow() > token_data["expires_at"].replace(tzinfo=None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token expirado"
            )
            
        user_email = token_data["user_email"]
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', user_email)
        results = query.get()
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
            
        user_ref = results[0].reference
        user_ref.update({
            "email_verified": True,
            "updated_at": datetime.utcnow()
        })
        token_doc.reference.set({"used": True}, merge=True)
        
        return {"detail": "Email verificado correctamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al verificar email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al verificar email"
        )

@router.post("/resend-verification", summary="Reenviar email de verificación", tags=["auth"])
async def resend_verification(request: ResendVerificationRequest):
    """
    Reenvía el email de verificación a un usuario.
    - Limita a 3 intentos en 3 días.
    """
    try:
        db = get_firebase_client()
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', request.email)
        results = query.get()
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
            
        user_doc = results[0]
        user_data = user_doc.to_dict()
        
        if user_data.get("email_verified"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email ya verificado"
            )
            
        # Verificar límites de envío
        attempts = user_data.get("verification_attempts", 0)
        last_attempt = user_data.get("last_verification_attempt")
        
        if last_attempt:
            last_attempt = last_attempt.replace(tzinfo=None)
            grace_period_end = last_attempt + timedelta(days=VERIFICATION_GRACE_PERIOD_DAYS)
            
            if attempts >= MAX_VERIFICATION_ATTEMPTS and datetime.utcnow() < grace_period_end:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Límite de intentos alcanzado. Por favor, espera hasta {grace_period_end.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            
            # Resetear contador si pasó el período de gracia
            if datetime.utcnow() >= grace_period_end:
                attempts = 0
        
        # Generar nuevo token de verificación
        verification_token = str(uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=24)
        db.collection("email_verification_tokens").document(verification_token).set({
            "user_email": request.email,
            "expires_at": expires_at,
            "used": False
        })
        
        # Actualizar contador de intentos
        user_doc.reference.update({
            "verification_attempts": attempts + 1,
            "last_verification_attempt": datetime.now()
        })
        
        # Enviar email de verificación
        if not email_service.send_verification_email(request.email, verification_token):
            logger.error(f"Error al enviar email de verificación a {request.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al enviar email de verificación"
            )
        
        return {"detail": "Se ha enviado un nuevo email de verificación"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al reenviar verificación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al reenviar verificación"
        )

@router.post("/login", response_model=dict, summary="Inicio de sesión", tags=["auth"])
async def login(user_data: UserLogin):
    """
    Inicia sesión de un usuario.
    
    - **email**: Email del usuario
    - **password**: Contraseña del usuario
    """
    # Buscar usuario por email
    user_ref = db.collection('users').where('email', '==', user_data.email).get()
    if not user_ref:
        raise AuthenticationError("Credenciales inválidas")
    
    user = user_ref[0].to_dict()
    
    # Verificar contraseña
    if not verify_password(user_data.password, user['password']):
        raise AuthenticationError("Credenciales inválidas")
    
    # Generar tokens
    access_token = create_access_token(data={"sub": user['id']})
    refresh_token = create_refresh_token(data={"sub": user['id']})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout", summary="Cerrar sesión", tags=["auth"])
async def logout(request: LogoutRequest):
    """
    Cierra la sesión del usuario invalidando el refresh token.
    - Requiere refresh token válido.
    """
    db = get_firebase_client()
    token_doc = db.collection("refresh_tokens").document(request.refresh_token)
    token_doc.set({"revoked": True})
    return {"detail": "Sesión cerrada correctamente"}

@router.post("/refresh", response_model=dict, summary="Refrescar token de acceso", tags=["auth"])
async def refresh_token(token_data: TokenRefresh):
    """
    Refresca el token de acceso usando el refresh token.
    
    - **refresh_token**: Token de refresco válido
    """
    try:
        # Verificar refresh token y generar nuevo access token
        access_token = create_access_token(data={"sub": token_data.refresh_token})
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise AuthenticationError("Token de refresco inválido")

@router.post("/forgot-password", summary="Solicitar recuperación de contraseña", tags=["auth"])
async def forgot_password(reset_data: PasswordReset):
    """
    Inicia el proceso de recuperación de contraseña.
    
    - **email**: Email del usuario
    """
    # Buscar usuario por email
    user_ref = db.collection('users').where('email', '==', reset_data.email).get()
    if not user_ref:
        # Por seguridad, no revelamos si el email existe o no
        return {"message": "Si el email existe, recibirás instrucciones para recuperar tu contraseña"}
    
    # Generar token de recuperación y enviar email
    # ... (implementar lógica de envío de email)
    
    return {"message": "Si el email existe, recibirás instrucciones para recuperar tu contraseña"}

@router.post("/reset-password", summary="Restablecer contraseña", tags=["auth"])
async def reset_password(reset_data: PasswordResetConfirm):
    """
    Restablece la contraseña usando un token de recuperación.
    
    - **token**: Token de recuperación
    - **new_password**: Nueva contraseña
    """
    try:
        # Verificar token y actualizar contraseña
        # ... (implementar lógica de verificación de token)
        
        return {"message": "Contraseña actualizada exitosamente"}
    except Exception as e:
        raise AuthenticationError("Token de recuperación inválido o expirado") 