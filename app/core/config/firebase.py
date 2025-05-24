import os
import json
import time
import firebase_admin
from firebase_admin import credentials, initialize_app, storage, firestore, auth, _apps
from app.core.config import settings
import logging
from typing import Optional, Any, Dict, Tuple
from datetime import datetime
from google.cloud import firestore as cloud_firestore
from pathlib import Path
from dotenv import load_dotenv
from app.services.firestore_mock import get_mock_firestore_client

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_credentials(cred_dict: Dict[str, Any]) -> bool:
    """
    Valida que las credenciales tengan todos los campos requeridos y el formato correcto.
    
    Args:
        cred_dict: Diccionario con las credenciales
        
    Returns:
        bool: True si las credenciales son válidas, False en caso contrario
    """
    required_fields = {
        "type": "service_account",
        "project_id": str,
        "private_key_id": str,
        "private_key": str,
        "client_email": str,
        "client_id": str,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": str
    }
    
    try:
        for field, expected_type in required_fields.items():
            if field not in cred_dict:
                logger.error(f"Campo requerido faltante: {field}")
                return False
            if isinstance(expected_type, type) and not isinstance(cred_dict[field], expected_type):
                logger.error(f"Tipo incorrecto para {field}: esperado {expected_type}, obtenido {type(cred_dict[field])}")
                return False
            if isinstance(expected_type, str) and cred_dict[field] != expected_type:
                logger.error(f"Valor incorrecto para {field}: esperado {expected_type}, obtenido {cred_dict[field]}")
                return False
        return True
    except Exception as e:
        logger.error(f"Error al validar credenciales: {str(e)}")
        return False

def initialize_firebase():
    """
    Inicializa la aplicación de Firebase Admin SDK.
    """
    try:
        # Verificar si Firebase ya está inicializado
        if _apps:
            logger.info("Firebase ya está inicializado")
            return
            
        # Obtener la ruta del archivo de credenciales
        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
        if not cred_path:
            raise ValueError("FIREBASE_CREDENTIALS_PATH no está configurado")
            
        # Verificar que el archivo existe
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"No se encontró el archivo de credenciales en {cred_path}")
            
        # Inicializar Firebase con las credenciales
        cred = credentials.Certificate(cred_path)
        initialize_app(cred, {
            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
        })
        logger.info("Firebase inicializado correctamente")
        
    except Exception as e:
        logger.error(f"Error al inicializar Firebase: {str(e)}")
        raise

def get_firestore_client():
    """Obtiene el cliente de Firestore."""
    if not _apps:
        initialize_firebase()
    return firestore.client()

def get_storage_client():
    """Obtiene el cliente de Storage."""
    if not _apps:
        initialize_firebase()
    return storage.bucket()

def get_auth_client():
    """Obtiene el cliente de Auth."""
    if not _apps:
        initialize_firebase()
    return auth

def get_firebase_client() -> Tuple[firestore.Client, auth.Client, Any]:
    """
    Obtiene los clientes de Firestore, Auth y Storage.
    
    Returns:
        Tuple[firestore.Client, auth.Client, Any]: Clientes de Firestore, Auth y Storage
    """
    try:
        if not _apps:
            initialize_firebase()
        db = firestore.client()
        auth_client = auth.Client()
        storage_bucket = storage.bucket()
        return db, auth_client, storage_bucket
    except Exception as e:
        logger.error(f"Error al obtener clientes de Firebase: {str(e)}")
        raise

def get_storage_bucket() -> Any:
    """
    Obtiene el bucket de Firebase Storage.
    
    Returns:
        Any: Bucket de Firebase Storage.
    """
    try:
        app = firebase_admin.get_app()
        bucket = storage.bucket()
        if bucket is None:
            logger.error("El bucket de Storage es None")
            raise ValueError("El bucket de Storage no se pudo inicializar")
        logger.info("Bucket de Storage obtenido correctamente")
        return bucket
    except Exception as e:
        logger.error(f"Error al obtener bucket de Storage: {str(e)}")
        raise

def create_user_document(db: Any, user_id: str, user_data: dict) -> str:
    """
    Crea un documento de usuario en Firestore.
    
    Args:
        db: Cliente de Firestore
        user_id: ID del usuario
        user_data: Datos del usuario
        
    Returns:
        str: ID del documento creado
    """
    try:
        user_ref = db.collection('users').document(user_id)
        user_data.update({
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        user_ref.set(user_data)
        return user_id
    except Exception as e:
        logger.error(f"Error al crear documento de usuario: {str(e)}")
        raise

def update_user_document(db: Any, user_id: str, user_data: dict) -> None:
    """
    Actualiza un documento de usuario en Firestore.
    
    Args:
        db: Cliente de Firestore
        user_id: ID del usuario
        user_data: Datos del usuario a actualizar
    """
    try:
        user_ref = db.collection('users').document(user_id)
        user_data.update({
            'updated_at': datetime.utcnow()
        })
        user_ref.update(user_data)
    except Exception as e:
        logger.error(f"Error al actualizar documento de usuario: {str(e)}")
        raise

def get_user_document(user_id: str) -> firestore.DocumentReference:
    """
    Obtiene una referencia al documento del usuario en Firestore.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        firestore.DocumentReference: Referencia al documento del usuario
    """
    try:
        db, _, _ = get_firebase_client()
        return db.collection('users').document(user_id)
    except Exception as e:
        logger.error(f"Error al obtener documento de usuario: {str(e)}")
        raise