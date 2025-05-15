import logging
from app.config.firebase import initialize_firebase
from firebase_admin import firestore, storage
from app.core.config import settings
from typing import Optional
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def get_firebase_client():
    """Obtiene una instancia del cliente de Firestore."""
    return firestore.client()

def get_storage_client():
    """Obtiene una instancia del cliente de Storage."""
    return storage.bucket(settings.FIREBASE_STORAGE_BUCKET)

def get_db():
    try:
        return initialize_firebase()
    except Exception as e:
        logger.error(f"Error getting Firestore client: {str(e)}")
        return None

def create_user(user_data: dict) -> Optional[str]:
    """
    Crea un nuevo usuario en Firestore usando el email como ID del documento.
    """
    try:
        db = get_firebase_client()
        users_ref = db.collection('users')
        
        # Verificar si el email ya existe
        existing_user = get_user_by_email(user_data['email'])
        if existing_user:
            raise ValueError("El email ya está registrado")
            
        # Crear documento de usuario usando el email como ID
        user_ref = users_ref.document(user_data['email'])
        
        # Preparar datos del usuario con valores por defecto
        user_data.update({
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True,
            'is_verified': False,
            'fecha_registro': datetime.utcnow(),
            'preferences': {
                'notifications': True,
                'email_notifications': True,
                'language': 'es',
                'timezone': 'UTC'
            },
            'stats': {
                'matches_played': 0,
                'matches_won': 0,
                'total_points': 0
            },
            'achievements': [],
            'blocked_users': [],
            'clubs': [],
            'availability': [],
            'onboarding_status': 'pending'
        })
        
        user_ref.set(user_data)
        return user_ref.id
    except Exception as e:
        logger.error(f"Error al crear usuario: {str(e)}")
        raise 

def get_user_by_email(email: str) -> Optional[dict]:
    """
    Obtiene un usuario por su email.
    """
    try:
        db = get_firebase_client()
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', email).limit(1)
        results = query.get()
        
        if not results:
            return None
            
        user_doc = results[0]
        user_data = user_doc.to_dict()
        user_data['id'] = user_doc.id
        return user_data
    except Exception as e:
        logger.error(f"Error al obtener usuario por email: {str(e)}")
        return None 

def create_user_document(user_data: dict):
    """Crea un documento de usuario en Firestore."""
    db = get_firebase_client()
    user_ref = db.collection('users').document()
    user_data.update({
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'is_active': True,
        'is_verified': False
    })
    user_ref.set(user_data)
    return user_ref.id

def update_user_document(user_id: str, update_data: dict):
    """Actualiza un documento de usuario en Firestore."""
    db = get_firebase_client()
    user_ref = db.collection('users').document(user_id)
    update_data['updated_at'] = datetime.utcnow()
    user_ref.update(update_data) 