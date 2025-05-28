from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.user import UserInDB
from app.services.firebase import get_firebase_client
from app.core.config import settings
from app.core.security import decode_token
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """
    Obtiene el usuario actual basado en el token.
    En desarrollo, acepta tokens JWT locales.
    En producción, usa Firebase Authentication.
    """
    try:
        token = credentials.credentials
        db, auth_client = get_firebase_client()
        
        if settings.ENVIRONMENT == "development":
            # En desarrollo, usar JWT local
            try:
                payload = decode_token(token)
                user_id = payload.get("sub")
                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token inválido",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            except Exception as e:
                logger.error(f"Error decodificando token JWT: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        else:
            # En producción, usar Firebase
            try:
                decoded_token = auth_client.verify_id_token(token)
                user_id = decoded_token['uid']
            except Exception as e:
                logger.error(f"Error verificando token Firebase: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        # Obtener datos del usuario de Firestore
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
            
        user_data = user_doc.to_dict()
        user_data['id'] = user_id
        return UserInDB(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en autenticación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        ) 