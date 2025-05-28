import os
import firebase_admin
from firebase_admin import credentials, auth
from app.core.config import settings

_firebase_app = None

def initialize_firebase():
    """
    Inicializa la conexión con Firebase.
    """
    global _firebase_app
    
    if _firebase_app is None:
        try:
            # Verificar si ya existe una aplicación inicializada
            _firebase_app = firebase_admin.get_app()
        except ValueError:
            # Si no existe, crear una nueva aplicación
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "private_key": settings.FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
                "client_email": settings.FIREBASE_CLIENT_EMAIL
            })
            _firebase_app = firebase_admin.initialize_app(cred)
    
    return _firebase_app

def get_firebase_app():
    """
    Obtiene la instancia de la aplicación Firebase.
    """
    if _firebase_app is None:
        return initialize_firebase()
    return _firebase_app 