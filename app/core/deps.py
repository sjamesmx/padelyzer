from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.user import UserInDB
from app.services.firebase import get_firebase_client
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """
    Obtiene el usuario actual basado en el token de Firebase.
    """
    try:
        token = credentials.credentials
        db, auth_client = get_firebase_client()
        
        # Verificar el token con Firebase Admin
        try:
            decoded_token = auth_client.verify_id_token(token)
            user_id = decoded_token['uid']
        except Exception as e:
            logger.error(f"Error verificando token: {str(e)}")
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