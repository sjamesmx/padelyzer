"""
Módulo de autenticación para la aplicación.
Proporciona funciones para la validación de tokens y obtención del usuario actual.
"""

import logging
from typing import Optional, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from app.core.config.firebase import get_firebase_clients

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Obtiene el usuario actual basado en el token de Firebase.
    
    Args:
        credentials: Credenciales HTTP que contienen el token
        
    Returns:
        Dict: Datos del usuario autenticado
        
    Raises:
        HTTPException: Si el token es inválido o ha expirado
    """
    try:
        # Obtener el cliente de Auth
        _, auth_client = get_firebase_clients()
        
        # Verificar el token
        token = credentials.credentials
        decoded_token = auth_client.verify_id_token(token)
        
        # Obtener información del usuario
        user = auth_client.get_user(decoded_token['uid'])
        
        return {
            'uid': user.uid,
            'email': user.email,
            'email_verified': user.email_verified,
            'display_name': user.display_name,
            'photo_url': user.photo_url
        }
        
    except auth.InvalidIdTokenError:
        logger.error("Token inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )
    except auth.ExpiredIdTokenError:
        logger.error("Token expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except auth.RevokedIdTokenError:
        logger.error("Token revocado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revocado"
        )
    except Exception as e:
        logger.error(f"Error al verificar token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error al verificar token"
        )

def verify_firebase_token(token: str) -> Optional[Dict]:
    """
    Verifica un token de Firebase y devuelve la información del usuario.
    
    Args:
        token: Token de Firebase a verificar
        
    Returns:
        Optional[Dict]: Datos del usuario si el token es válido, None en caso contrario
    """
    try:
        # Obtener el cliente de Auth
        _, auth_client = get_firebase_clients()
        
        # Verificar el token
        decoded_token = auth_client.verify_id_token(token)
        
        # Obtener información del usuario
        user = auth_client.get_user(decoded_token['uid'])
        
        return {
            'uid': user.uid,
            'email': user.email,
            'email_verified': user.email_verified,
            'display_name': user.display_name,
            'photo_url': user.photo_url
        }
        
    except Exception as e:
        logger.error(f"Error al verificar token: {str(e)}")
        return None 