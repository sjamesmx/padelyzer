import logging
import firebase_admin
from firebase_admin import credentials
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_firebase():
    """Inicializa la aplicación de Firebase."""
    logger.info("Starting firebase.py import process")
    # Obtener la ruta del directorio actual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.join(current_dir, "firebase-service-account.json")
    logger.info(f"Checking credential path: {cred_path}")
    
    try:
        cred = credentials.Certificate(cred_path)
        logger.info("Loaded credentials")
        firebase_admin.initialize_app(cred)
        logger.info("Initialized Firebase app")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {str(e)}")
        raise