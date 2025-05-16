import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_firebase_connection():
    try:
        # Load environment variables
        load_dotenv()
        
        # Get credentials path from environment variable
        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
        if not cred_path:
            raise ValueError("FIREBASE_CREDENTIALS_PATH environment variable is not set")
            
        logger.info(f"Usando credenciales desde: {cred_path}")
        
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

        # Probar la conexión a Firestore
        db = firestore.client()
        users_ref = db.collection("users").limit(1).get()
        logger.info("Conexión a Firestore exitosa!")
        
        return True
    except Exception as e:
        logger.error(f"Error al conectar a Firestore: {str(e)}")
        raise

if __name__ == "__main__":
    test_firebase_connection() 