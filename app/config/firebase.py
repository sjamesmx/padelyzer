"""
Configuración y inicialización de Firebase para la aplicación Padelyzer.

Este módulo se encarga de inicializar la conexión con Firebase
y proporciona funciones para obtener clientes de Firestore y Storage.
"""

import os
import logging
from typing import Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore, storage

logger = logging.getLogger(__name__)

def initialize_firebase() -> firestore.Client:
    """
    Inicializa Firebase Admin SDK con las credenciales configuradas.

    Returns:
        Cliente de Firestore inicializado

    Raises:
        Exception: Si hay un error al inicializar Firebase
    """
    if firebase_admin._apps:
        return firestore.client()

    try:
        # Usar emulador si está disponible
        if os.getenv('FIRESTORE_EMULATOR_HOST'):
            logger.info(f"Usando Firestore emulator en {os.getenv('FIRESTORE_EMULATOR_HOST')}")
            firebase_admin.initialize_app(options={
                'projectId': os.getenv('FIREBASE_PROJECT_ID', 'padelyzer-test')
            })
        else:
            # Usar credenciales desde archivo o variables de entorno
            if os.getenv('FIREBASE_CREDENTIALS_PATH'):
                cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH'))
            elif all([
                os.getenv('FIREBASE_PROJECT_ID'),
                os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                os.getenv('FIREBASE_PRIVATE_KEY'),
                os.getenv('FIREBASE_CLIENT_EMAIL')
            ]):
                cred = credentials.Certificate({
                    "type": "service_account",
                    "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                    "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                    "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
                    "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                    "client_id": os.getenv('FIREBASE_CLIENT_ID', ""),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL', ""),
                })
            else:
                raise ValueError("No se encontraron credenciales de Firebase")

            storage_bucket = os.getenv(
                'FIREBASE_STORAGE_BUCKET',
                f"{os.getenv('FIREBASE_PROJECT_ID', 'padelyzer')}.firebasestorage.app"
            )
            firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket
            })

        logger.info("Firebase inicializado correctamente")
        return firestore.client()
    except Exception as e:
        logger.error(f"Error al inicializar Firebase: {str(e)}")
        raise

def get_firebase_clients() -> Dict[str, Any]:
    """
    Obtiene clientes de Firestore y Storage.

    Returns:
        Dict con los clientes de Firestore y Storage
    """
    if not firebase_admin._apps:
        initialize_firebase()
    return {
        'db': firestore.client(),
        'storage': storage.bucket()
    }

def get_firestore_client() -> firestore.Client:
    """
    Obtiene cliente de Firestore.
    """
    return initialize_firebase()
