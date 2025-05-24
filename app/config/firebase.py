"""
Configuración de Firebase para la aplicación Padelyzer.

Este módulo proporciona funciones para inicializar Firebase Admin SDK
y obtener clientes de Firestore y Storage.
"""

import firebase_admin
from firebase_admin import credentials, firestore, storage
from typing import Tuple, Optional
import os
import logging

logger = logging.getLogger(__name__)

def initialize_firebase() -> None:
    """
    Inicializa Firebase Admin SDK con las credenciales configuradas.

    Raises:
        Exception: Si hay un error al inicializar Firebase
    """
    if not firebase_admin._apps:
        try:
            # Intentar usar credenciales de variables de entorno
            if os.getenv('FIREBASE_CREDENTIALS_PATH'):
                cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH'))
            # Alternativa: usar credenciales en línea
            elif all([
                os.getenv('FIREBASE_PROJECT_ID'),
                os.getenv('FIREBASE_PRIVATE_KEY'),
                os.getenv('FIREBASE_CLIENT_EMAIL')
            ]):
                cred = credentials.Certificate({
                    "type": "service_account",
                    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                    "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
                    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL')
                })
            else:
                raise ValueError("No se encontraron credenciales de Firebase")

            firebase_admin.initialize_app(cred, {
                'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', f"{os.getenv('FIREBASE_PROJECT_ID')}.appspot.com")
            })
            logger.info("Firebase inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar Firebase: {str(e)}")
            raise

def get_firebase_client() -> Tuple[firestore.Client, storage.Client]:
    """
    Obtiene clientes de Firestore y Storage.

    Returns:
        Tuple con el cliente de Firestore y el cliente de Storage

    Raises:
        Exception: Si hay un error al obtener los clientes
    """
    if not firebase_admin._apps:
        initialize_firebase()

    try:
        db = firestore.client()
        bucket = storage.bucket()
        return db, bucket
    except Exception as e:
        logger.error(f"Error al obtener clientes de Firebase: {str(e)}")
        raise
