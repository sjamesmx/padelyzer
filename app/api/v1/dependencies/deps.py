from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings
from app.services.firebase import get_firebase_client
from app.schemas.user import UserInDB
import logging

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        logger.info(f"Decodificando token: {token[:10]}...")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.error("Token no contiene sub claim")
            raise credentials_exception
        logger.info(f"Token decodificado correctamente. user_id: {user_id}")
    except JWTError as e:
        logger.error(f"Error decodificando token: {str(e)}")
        raise credentials_exception
    try:
        db = get_firebase_client()
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            logger.error(f"Usuario no encontrado en Firestore: {user_id}")
            raise credentials_exception
        user_data = user_doc.to_dict()
        user_data['id'] = user_doc.id
        logger.info(f"Usuario encontrado en Firestore: {user_id}")
        return UserInDB(**user_data)
    except Exception as e:
        logger.error(f"Error obteniendo usuario de Firestore: {str(e)}")
        raise credentials_exception 