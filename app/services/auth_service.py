from typing import Optional, Tuple
from fastapi import HTTPException
from firebase_admin import auth
from app.schemas.auth import UserCreate, UserResponse
import logging
from app.core.config.firebase import get_firebase_clients
import firebase_admin
from firebase_admin import credentials
import requests
import os
from datetime import datetime, timezone, timedelta
import re
from uuid import uuid4

logger = logging.getLogger(__name__)

def verify_firebase_token(token: str) -> dict:
    """
    Verifica un token de Firebase y retorna la información del usuario.
    """
    try:
        clients = get_firebase_clients()
        auth_client = clients['auth']
        decoded_token = auth_client.verify_id_token(token)
        return decoded_token
    except Exception as e:
        import traceback
        logger.error(f"Error al verificar token de Firebase: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado"
        )

def get_user_by_token(token: str) -> Optional[dict]:
    """
    Obtiene un usuario por su token de Firebase.
    """
    try:
        decoded_token = verify_firebase_token(token)
        user_id = decoded_token.get('uid')
        if not user_id:
            return None
        clients = get_firebase_clients()
        db = clients['db']
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        if not user_doc.exists:
            return None
        user_data = user_doc.to_dict()
        user_data['id'] = user_doc.id
        return user_data
    except Exception as e:
        logger.error(f"Error al obtener usuario por token: {str(e)}")
        return None 

def get_id_token(email: str, password: str) -> str:
    """
    Obtiene un ID token usando las credenciales de Firebase.
    """
    try:
        # API key de Firebase
        api_key = "AIzaSyAFSKgCPMCrg7D_z5HGYJinGWv1aIp5-o8"

        # Hacer la petición a la API de Firebase Auth
        response = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
            json={
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Error al obtener ID token: {response.text}")
            
        return response.json()["idToken"]
    except Exception as e:
        logger.error(f"Error al obtener ID token: {str(e)}")
        raise

def validate_password(password: str, email: str):
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    if email and password.lower() == email.lower():
        raise ValueError("La contraseña no puede ser igual al email.")
    if ' ' in password:
        raise ValueError("La contraseña no puede contener espacios en blanco.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("La contraseña debe contener al menos una letra mayúscula.")
    if not re.search(r"[a-z]", password):
        raise ValueError("La contraseña debe contener al menos una letra minúscula.")
    if not re.search(r"[0-9]", password):
        raise ValueError("La contraseña debe contener al menos un número.")
    if not re.search(r"[!@#$%^&*()\-_=+\[\]{};:,.<>?/|]", password):
        raise ValueError("La contraseña debe contener al menos un carácter especial.")

class AuthService:
    @staticmethod
    async def register_user(user_data: UserCreate) -> Tuple[Optional[UserResponse], Optional[str]]:
        """
        Registra un nuevo usuario en Firebase Auth.
        Retorna una tupla con (usuario, error)
        """
        try:
            validate_password(user_data.password, user_data.email)
            # Crear usuario en Firebase Auth
            user = auth.create_user(
                email=user_data.email,
                password=user_data.password,
                display_name=user_data.display_name
            )

            # Guardar usuario en Firestore (solo datos básicos)
            clients = get_firebase_clients()
            db = clients['db']
            user_doc = {
                "email": user.email,
                "display_name": user.display_name,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "photo_url": user.photo_url
            }
            db.collection('users').document(user.uid).set(user_doc)
            
            # Crear respuesta con datos del usuario
            user_response = UserResponse(
                uid=user.uid,
                email=user.email,
                display_name=user.display_name,
                photo_url=user.photo_url
            )
            
            return user_response, None
            
        except Exception as e:
            logger.error(f"Error al registrar usuario: {str(e)}")
            return None, str(e)

    @staticmethod
    async def login_user(email: str, password: str, ip: str = None, user_agent: str = None) -> Tuple[Optional[dict], Optional[str]]:
        """
        Autentica un usuario y retorna un token.
        Registra la sesión en Firestore.
        """
        try:
            # Obtener usuario y verificar credenciales
            user = auth.get_user_by_email(email)
            # Obtener ID token
            id_token = get_id_token(email, password)
            # Registrar sesión en Firestore
            clients = get_firebase_clients()
            db = clients['db']
            session_id = str(uuid4())
            now = datetime.now(timezone.utc).isoformat()
            session_doc = {
                "user_id": user.uid,
                "session_id": session_id,
                "created_at": now,
                "last_active": now,
                "is_active": True,
                "ip": ip,
                "user_agent": user_agent
            }
            db.collection('sessions').document(session_id).set(session_doc)
            return {
                "access_token": id_token,
                "token_type": "bearer",
                "user": UserResponse(
                    uid=user.uid,
                    email=user.email,
                    display_name=user.display_name,
                    photo_url=user.photo_url
                ),
                "session_id": session_id
            }, None
        except Exception as e:
            logger.error(f"Error al iniciar sesión: {str(e)}")
            return None, str(e)

    @staticmethod
    async def get_current_user(token: str) -> Tuple[Optional[UserResponse], Optional[str]]:
        """
        Verifica un token y retorna el usuario actual.
        Retorna una tupla con (usuario, error)
        """
        try:
            # Verificar token y obtener usuario
            decoded_token = auth.verify_id_token(token)
            user = auth.get_user(decoded_token['uid'])
            
            return UserResponse(
                uid=user.uid,
                email=user.email,
                display_name=user.display_name,
                photo_url=user.photo_url
            ), None
            
        except Exception as e:
            logger.error(f"Error al obtener usuario actual: {str(e)}")
            return None, str(e)

    @staticmethod
    async def send_verification_email(user):
        # ... código existente ...
        # Cambiar expiración a 72 horas
        expires_at = datetime.now(timezone.utc) + timedelta(hours=72)
        # ... resto del código para guardar el token y enviar email ... 