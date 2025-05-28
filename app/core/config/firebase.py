"""
Configuración unificada de Firebase para la aplicación Padelyzer.

Este módulo es la única fuente de verdad para la configuración de Firebase
y proporciona funciones para inicializar y obtener clientes de Firebase.
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
from functools import lru_cache
from pathlib import Path
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseConfigError(Exception):
    """Excepción personalizada para errores de configuración de Firebase."""
    pass

class FirebaseInitializationError(Exception):
    """Excepción personalizada para errores de inicialización de Firebase."""
    pass

@lru_cache()
def get_firebase_credentials() -> credentials.Certificate:
    """
    Obtiene las credenciales de Firebase desde el archivo de configuración.
    Usa lru_cache para evitar leer el archivo múltiples veces.
    
    Returns:
        credentials.Certificate: Credenciales de Firebase
        
    Raises:
        FirebaseConfigError: Si hay un error al cargar las credenciales
    """
    try:
        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
        if not cred_path:
            raise FirebaseConfigError("FIREBASE_CREDENTIALS_PATH no está configurado")
            
        if not os.path.exists(cred_path):
            raise FirebaseConfigError(f"No se encontró el archivo de credenciales en {cred_path}")
            
        return credentials.Certificate(cred_path)
    except Exception as e:
        logger.error(f"Error al cargar credenciales de Firebase: {str(e)}")
        raise FirebaseConfigError(f"Error al cargar credenciales: {str(e)}")

def initialize_firebase() -> None:
    """
    Inicializa la aplicación de Firebase Admin SDK.
    
    Raises:
        FirebaseInitializationError: Si hay un error al inicializar Firebase
    """
    try:
        # Verificar si Firebase ya está inicializado
        if firebase_admin._apps:
            logger.info("Firebase ya está inicializado")
            return
            
        # Obtener credenciales
        cred = get_firebase_credentials()
        
        # Configurar opciones de inicialización
        options = {
            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'pdzr-458820.firebasestorage.app')
        }
        
        # Inicializar Firebase
        firebase_admin.initialize_app(cred, options)
        logger.info("Firebase inicializado correctamente")
        
    except Exception as e:
        logger.error(f"Error al inicializar Firebase: {str(e)}")
        raise FirebaseInitializationError(f"Error al inicializar Firebase: {str(e)}")

@lru_cache()
def get_firebase_clients() -> Dict[str, Any]:
    """
    Obtiene los clientes de Firebase (Firestore, Auth, Storage).
    Usa lru_cache para evitar múltiples inicializaciones.
    
    Returns:
        Dict[str, Any]: Diccionario con los clientes de Firebase
        
    Raises:
        FirebaseInitializationError: Si hay un error al obtener los clientes
    """
    try:
        if not firebase_admin._apps:
            initialize_firebase()
            
        # Obtener la aplicación de Firebase
        app = firebase_admin.get_app()
            
        return {
            'db': firestore.client(),
            'auth': auth.Client(app),
            'storage': storage.bucket()
        }
    except Exception as e:
        logger.error(f"Error al obtener clientes de Firebase: {str(e)}")
        raise FirebaseInitializationError(f"Error al obtener clientes: {str(e)}")

def verify_firebase_connection() -> bool:
    """
    Verifica la conexión con Firebase realizando una operación simple.
    
    Returns:
        bool: True si la conexión es exitosa, False en caso contrario
    """
    try:
        clients = get_firebase_clients()
        # Intentar una operación simple en Firestore
        clients['db'].collection('_health_check').document('test').get()
        return True
    except Exception as e:
        logger.error(f"Error al verificar conexión con Firebase: {str(e)}")
        return False

def get_health_status() -> Dict[str, Any]:
    """
    Obtiene el estado de salud de la conexión con Firebase.
    
    Returns:
        Dict[str, Any]: Diccionario con el estado de salud
    """
    try:
        clients = get_firebase_clients()
        firestore_ok = verify_firebase_connection()
        
        return {
            'status': 'healthy' if firestore_ok else 'unhealthy',
            'components': {
                'firestore': 'connected' if firestore_ok else 'disconnected',
                'auth': 'initialized' if clients['auth'] else 'not_initialized',
                'storage': 'initialized' if clients['storage'] else 'not_initialized'
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error al obtener estado de salud: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }