# test_firebase_credentials.py
import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging
from google.api_core.exceptions import GoogleAPIError, PermissionDenied, InvalidArgument

# Configurar logging para mostrar mensajes detallados
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_firebase_credentials():
    try:
        # Obtener la ruta del archivo de credenciales desde la variable de entorno
        cred_path = os.getenv("FIREBASE_CRED_PATH")
        if not cred_path:
            raise ValueError("FIREBASE_CRED_PATH no está configurado en las variables de entorno")

        # Verificar si el archivo existe
        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"El archivo de credenciales no existe: {cred_path}")

        logger.info(f"Usando archivo de credenciales: {cred_path}")

        # Cargar las credenciales
        cred = credentials.Certificate(cred_path)

        # Inicializar Firebase
        firebase_admin.initialize_app(cred)
        logger.info("Firebase inicializado correctamente")

        # Conectar a Firestore
        db = firestore.client()
        logger.info("Conexión a Firestore establecida")

        # Realizar una operación de escritura de prueba
        test_collection = "test_credentials"
        test_doc = "test_doc"
        test_data = {
            "test_field": "Este es un documento de prueba",
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        db.collection(test_collection).document(test_doc).set(test_data)
        logger.info(f"Documento de prueba escrito en Firestore: {test_collection}/{test_doc}")

        # Realizar una operación de lectura de prueba
        doc_ref = db.collection(test_collection).document(test_doc)
        doc = doc_ref.get()
        if doc.exists:
            logger.info(f"Documento de prueba leído correctamente: {doc.to_dict()}")
        else:
            logger.error("No se pudo leer el documento de prueba")

        # Limpiar: Eliminar el documento de prueba
        doc_ref.delete()
        logger.info("Documento de prueba eliminado")

        return True, "Prueba de credenciales exitosa"

    except FileNotFoundError as e:
        return False, f"Error: {str(e)}"
    except ValueError as e:
        return False, f"Error: {str(e)}"
    except InvalidArgument as e:
        return False, f"Error: Credenciales inválidas o corruptas - {str(e)}"
    except PermissionDenied as e:
        return False, f"Error: Permisos insuficientes - {str(e)}"
    except GoogleAPIError as e:
        return False, f"Error de API de Google: {str(e)}"
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"

if __name__ == "__main__":
    success, message = test_firebase_credentials()
    if success:
        logger.info("✅ " + message)
    else:
        logger.error("❌ " + message)