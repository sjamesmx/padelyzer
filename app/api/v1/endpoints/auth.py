from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.core.security import create_access_token, verify_password, get_password_hash
from app.schemas.user import User, UserCreate, Token
from app.schemas.auth import (
    TokenRefreshRequest, TokenRefreshResponse, LogoutRequest, ForgotPasswordRequest, ResetPasswordRequest,
    EmailVerificationRequest, ResendVerificationRequest
)
from app.services.firebase import get_firebase_client
from app.services.email import email_service
from datetime import datetime, timedelta
import logging
from uuid import uuid4
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Constantes para límites de envío de emails
MAX_VERIFICATION_ATTEMPTS = 3
VERIFICATION_GRACE_PERIOD_DAYS = 3

@router.post("/signup", response_model=User, summary="Registro de usuario", tags=["auth"])
async def signup(user_in: UserCreate):
    """
    Registra un nuevo usuario en el sistema.
    - Requiere email, nombre, nivel, posición preferida y contraseña.
    - Devuelve los datos del usuario creado y el token de verificación.
    """
    try:
        db = get_firebase_client()
        if db is None:
            logger.error("No se pudo obtener el cliente de Firestore")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al conectar con la base de datos"
            )
        
        # Verificar si el usuario ya existe
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', user_in.email)
        results = query.get()
        
        if results:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Crear nuevo usuario
        user_ref = users_ref.document()
        user_data = {
            'email': user_in.email,
            'name': user_in.name,
            'nivel': user_in.nivel,
            'posicion_preferida': user_in.posicion_preferida,
            'fecha_registro': datetime.now(),
            'ultimo_analisis': None,
            'tipo_ultimo_analisis': None,
            'fecha_ultimo_analisis': None,
            'email_verified': False,
            'hashed_password': get_password_hash(user_in.password),
            'verification_attempts': 0,
            'last_verification_attempt': datetime.now()
        }
        user_ref.set(user_data)
        
        # Generar token de verificación
        verification_token = str(uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=24)
        db.collection("email_verification_tokens").document(verification_token).set({
            "user_email": user_in.email,
            "expires_at": expires_at,
            "used": False
        })
        
        # En desarrollo, devolver el token de verificación
        if settings.ENVIRONMENT == "development":
            return {
                **user_data,
                'id': user_ref.id,
                'verification_token': verification_token
            }
        
        # En producción, enviar email de verificación
        if not email_service.send_verification_email(user_in.email, verification_token):
            logger.error(f"Error al enviar email de verificación a {user_in.email}")
        
        return {**user_data, 'id': user_ref.id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al registrar usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar usuario: {str(e)}"
        )

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

@router.post("/login", response_model=TokenRefreshResponse, summary="Inicio de sesión", tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Inicia sesión de un usuario existente.
    - Requiere email y contraseña.
    - Verifica que el email esté verificado.
    - Devuelve un access token JWT para autenticación y un refresh token.
    """
    try:
        db = get_firebase_client()
        # Buscar usuario
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', form_data.username)
        results = query.get()
        if not results:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )
        user_doc = results[0]
        user_data = user_doc.to_dict()
        
        # Verificar email
        if not user_data.get("email_verified", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email no verificado. Por favor, verifica tu email antes de iniciar sesión."
            )
            
        # Validar contraseña
        if not verify_password(form_data.password, user_data['hashed_password']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )
            
        # Crear access token
        access_token = create_access_token(data={"sub": user_data['email']})
        # Crear refresh token
        refresh_token = str(uuid4())
        expires_at = datetime.utcnow() + timedelta(days=7)
        db.collection("refresh_tokens").document(refresh_token).set({
            "user_email": user_data['email'],
            "expires_at": expires_at,
            "revoked": False
        })
        return TokenRefreshResponse(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al iniciar sesión: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al iniciar sesión"
        )

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

@router.post("/refresh", response_model=TokenRefreshResponse, summary="Refrescar token de acceso", tags=["auth"])
async def refresh_token(request: TokenRefreshRequest):
    """
    Refresca el token de acceso usando un refresh token válido.
    - Devuelve un nuevo access token y refresh token.
    """
    db = get_firebase_client()
    token_doc = db.collection("refresh_tokens").document(request.refresh_token).get()
    if not token_doc.exists or token_doc.to_dict().get("revoked"):
        raise HTTPException(status_code=401, detail="Refresh token inválido o revocado")
    token_data = token_doc.to_dict()
    if datetime.utcnow() > token_data["expires_at"].replace(tzinfo=None):
        raise HTTPException(status_code=401, detail="Refresh token expirado")
    user_email = token_data["user_email"]
    access_token = create_access_token({"sub": user_email})
    # Opcional: emitir nuevo refresh token y revocar el anterior
    new_refresh_token = str(uuid4())
    expires_at = datetime.utcnow() + timedelta(days=7)
    db.collection("refresh_tokens").document(new_refresh_token).set({
        "user_email": user_email,
        "expires_at": expires_at,
        "revoked": False
    })
    token_doc.reference.set({"revoked": True}, merge=True)
    return TokenRefreshResponse(
        access_token=access_token,
        token_type="bearer",
        refresh_token=new_refresh_token
    )

@router.post("/forgot-password", summary="Solicitar recuperación de contraseña", tags=["auth"])
async def forgot_password(request: ForgotPasswordRequest):
    """
    Solicita la recuperación de contraseña para un usuario registrado.
    - Envía un email (simulado) con instrucciones y token de recuperación.
    """
    db = get_firebase_client()
    users_ref = db.collection('users')
    query = users_ref.where('email', '==', request.email)
    results = query.get()
    if not results:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    reset_token = str(uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)
    db.collection("password_reset_tokens").document(reset_token).set({
        "user_email": request.email,
        "expires_at": expires_at,
        "used": False
    })
    # Simulación de envío de email (en producción, integrar con un servicio real)
    logger.info(f"Token de recuperación para {request.email}: {reset_token}")
    return {"detail": "Se ha enviado un email con instrucciones para restablecer la contraseña"}

@router.post("/reset-password", summary="Restablecer contraseña", tags=["auth"])
async def reset_password(request: ResetPasswordRequest):
    """
    Restablece la contraseña de un usuario usando un token de recuperación válido.
    - Requiere token de recuperación y nueva contraseña.
    """
    db = get_firebase_client()
    token_doc = db.collection("password_reset_tokens").document(request.token).get()
    if not token_doc.exists:
        raise HTTPException(status_code=400, detail="Token de recuperación inválido")
    token_data = token_doc.to_dict()
    if token_data.get("used"):
        raise HTTPException(status_code=400, detail="Token ya utilizado")
    if datetime.utcnow() > token_data["expires_at"].replace(tzinfo=None):
        raise HTTPException(status_code=400, detail="Token expirado")
    user_email = token_data["user_email"]
    # Actualizar contraseña del usuario
    users_ref = db.collection('users')
    query = users_ref.where('email', '==', user_email)
    results = query.get()
    if not results:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user_ref = results[0].reference
    hashed_password = get_password_hash(request.new_password)
    user_ref.update({"hashed_password": hashed_password})
    token_doc.reference.set({"used": True}, merge=True)
    return {"detail": "Contraseña restablecida correctamente"} 