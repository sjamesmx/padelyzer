import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar las credenciales
os.environ["FIREBASE_CRED_PATH"] = "/Users/jaime/pdzr/backend/config/firebase-credentials.json"
cred = credentials.Certificate(os.getenv("FIREBASE_CRED_PATH"))
firebase_admin.initialize_app(cred)

# Probar la conexión a Firestore
try:
    db = firestore.client()
    users_ref = db.collection("users").limit(1).get()
    logger.info("Conexión a Firestore exitosa!")
except Exception as e:
    logger.error(f"Error al conectar a Firestore: {str(e)}")
    raise 