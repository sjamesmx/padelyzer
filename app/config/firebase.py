import os
import json
import time
import firebase_admin
from firebase_admin import credentials, initialize_app, storage, firestore
from app.core.config import settings
import logging
from typing import Optional, Any, Dict
from datetime import datetime
from google.cloud import firestore as cloud_firestore
from dotenv import load_dotenv

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
    Inicializa la conexión con Firebase usando variables de entorno.
    """
    try:
        # Cargar variables de entorno
        if "PYTEST_CURRENT_TEST" in os.environ:
            load_dotenv(".env.test")
        else:
            load_dotenv()
        
        # Verificar que todas las variables necesarias estén presentes
        required_vars = [
            'FIREBASE_PROJECT_ID',
            'FIREBASE_PRIVATE_KEY_ID',
            'FIREBASE_PRIVATE_KEY',
            'FIREBASE_CLIENT_EMAIL',
            'FIREBASE_CLIENT_ID',
            'FIREBASE_CLIENT_CERT_URL'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Faltan variables de entorno: {', '.join(missing_vars)}")
        
        # Crear diccionario de credenciales
        cred_dict = {
            "type": "service_account",
            "project_id": os.getenv('FIREBASE_PROJECT_ID'),
            "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
            "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
            "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
            "client_id": os.getenv('FIREBASE_CLIENT_ID'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL')
        }
        
        # Validar credenciales
        if not validate_credentials(cred_dict):
            raise ValueError("Credenciales de Firebase inválidas")
        
        # Inicializar Firebase solo si no está inicializado
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_dict)
            app = initialize_app(cred)
            logger.info("Firebase inicializado correctamente")
        
        return firestore.client()
        
    except Exception as e:
        logger.error(f"Error al inicializar Firebase: {str(e)}")
        raise

# Inicializar
db = initialize_firebase()

def get_firebase_client() -> Any:
    """
    Obtiene una instancia del cliente de Firestore.
    
    Returns:
        Any: Cliente de Firestore.
    """
    try:
        return firestore.client()
    except Exception as e:
        logger.error(f"Error al obtener cliente de Firestore: {str(e)}")
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

def get_user_document(db: Any, user_id: str) -> Optional[dict]:
    """
    Obtiene un documento de usuario de Firestore.
    
    Args:
        db: Cliente de Firestore
        user_id: ID del usuario
        
    Returns:
        Optional[dict]: Datos del usuario o None si no existe
    """
    try:
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        if user_doc.exists:
            return user_doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error al obtener documento de usuario: {str(e)}")
        raise 