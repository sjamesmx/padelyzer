from typing import Optional
from fastapi import HTTPException
from firebase_admin import auth
from firebase_admin import credentials
from firebase_admin import initialize_app
from firebase_admin import firestore
from firebase_admin import logger

def verify_firebase_token(token: str) -> dict:
    """
    Verifica un token de Firebase y retorna la información del usuario.
    """
    try:
        _, auth_client = get_firebase_client()
        decoded_token = auth_client.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Error al verificar token de Firebase: {str(e)}")
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
            
        db, _ = get_firebase_client()
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