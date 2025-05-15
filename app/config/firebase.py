import os
import json
import time
import firebase_admin
from firebase_admin import credentials, initialize_app, storage, firestore
from app.core.config import settings
import logging
from typing import Optional, Any, Dict
from datetime import datetime

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
                
            if isinstance(expected_type, type):
                if not isinstance(cred_dict[field], expected_type):
                    logger.error(f"Tipo incorrecto para {field}: esperado {expected_type}, recibido {type(cred_dict[field])}")
                    return False
            elif cred_dict[field] != expected_type:
                logger.error(f"Valor incorrecto para {field}: esperado {expected_type}, recibido {cred_dict[field]}")
                return False
                
        # Validar formato de private_key
        private_key = cred_dict.get('private_key', '')
        
        # Normalizar la clave privada
        private_key = private_key.replace('\\n', '\n').strip()
        
        # Verificar que la clave comience y termine correctamente
        if not any(private_key.startswith(prefix) for prefix in ['-----BEGIN PRIVATE KEY-----', '-----BEGIN RSA PRIVATE KEY-----']):
            logger.error("Formato incorrecto de private_key: debe comenzar con '-----BEGIN PRIVATE KEY-----' o '-----BEGIN RSA PRIVATE KEY-----'")
            return False
            
        if not any(private_key.endswith(suffix) for suffix in ['-----END PRIVATE KEY-----', '-----END RSA PRIVATE KEY-----']):
            logger.error("Formato incorrecto de private_key: debe terminar con '-----END PRIVATE KEY-----' o '-----END RSA PRIVATE KEY-----'")
            return False
            
        # Verificar que la clave tenga el formato correcto
        key_lines = private_key.split('\n')
        if len(key_lines) < 3:
            logger.error("Formato incorrecto de private_key: debe tener al menos 3 líneas")
            return False
            
        # Verificar que la clave base64 sea válida
        try:
            import base64
            key_content = ''.join(key_lines[1:-1])
            base64.b64decode(key_content)
        except Exception as e:
            logger.error(f"Formato incorrecto de private_key: contenido base64 inválido - {str(e)}")
            return False
            
        logger.info("✅ Formato de private_key válido")
        return True
    except Exception as e:
        logger.error(f"Error al validar credenciales: {str(e)}")
        return False

def initialize_firebase(max_retries: int = 3, retry_delay: int = 2) -> Optional[firebase_admin.App]:
    """
    Inicializa Firebase con las credenciales apropiadas.
    
    Args:
        max_retries: Número máximo de intentos de inicialización
        retry_delay: Tiempo de espera entre intentos en segundos
        
    Returns:
        Optional[firebase_admin.App]: La instancia de la aplicación de Firebase o None si hay un error.
    """
    for attempt in range(max_retries):
        try:
            # Limpiar cualquier instancia existente
            for app in firebase_admin._apps.values():
                try:
                    firebase_admin.delete_app(app)
                except Exception as e:
                    logger.warning(f"Error al eliminar app existente: {str(e)}")

            # Intentar primero con credenciales directas
            try:
                cred_dict = {
                    "type": "service_account",
                    "project_id": "pdzr-458820",
                    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
                    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
                }
                
                # Verificar que todas las variables de entorno necesarias estén presentes
                required_vars = ["FIREBASE_PRIVATE_KEY_ID", "FIREBASE_PRIVATE_KEY", 
                               "FIREBASE_CLIENT_EMAIL", "FIREBASE_CLIENT_ID", 
                               "FIREBASE_CLIENT_CERT_URL"]
                
                missing_vars = [var for var in required_vars if not os.getenv(var)]
                
                if not missing_vars and validate_credentials(cred_dict):
                    logger.info("Inicializando Firebase con credenciales de variables de entorno")
                    cred = credentials.Certificate(cred_dict)
                    app = initialize_app(cred, {
                        'storageBucket': settings.FIREBASE_STORAGE_BUCKET,
                        'databaseURL': settings.FIREBASE_DATABASE_URL
                    })
                    logger.info("Firebase inicializado correctamente con credenciales de variables de entorno")
                    return app
                else:
                    if missing_vars:
                        logger.warning(f"Faltan variables de entorno: {', '.join(missing_vars)}")
                    raise ValueError("Credenciales de variables de entorno inválidas")
                    
            except Exception as env_error:
                logger.warning(f"Error al usar credenciales de variables de entorno: {str(env_error)}")
                
                # Si falla, intentar con el archivo de credenciales
                cred_path = "/Users/dev4/pdzr/backend/config/firebase-credentials.json"
                logger.info(f"Intentando inicializar Firebase con credenciales desde archivo: {cred_path}")
                
                if not os.path.exists(cred_path):
                    logger.error(f"FIREBASE_CRED_PATH no existe: {cred_path}")
                    raise ValueError(f"FIREBASE_CRED_PATH no existe: {cred_path}")
                    
                # Validar el archivo de credenciales
                try:
                    with open(cred_path, 'r') as f:
                        cred_dict = json.load(f)
                    if not validate_credentials(cred_dict):
                        raise ValueError("Credenciales del archivo inválidas")
                except Exception as e:
                    logger.error(f"Error al validar archivo de credenciales: {str(e)}")
                    raise
                    
                cred = credentials.Certificate(cred_path)
                app = initialize_app(cred, {
                    'storageBucket': settings.FIREBASE_STORAGE_BUCKET,
                    'databaseURL': settings.FIREBASE_DATABASE_URL
                })
                logger.info("Firebase inicializado correctamente con credenciales de archivo")
                return app
                
        except Exception as e:
            logger.error(f"Error al inicializar Firebase (intento {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Reintentando en {retry_delay} segundos...")
                time.sleep(retry_delay)
            else:
                raise

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