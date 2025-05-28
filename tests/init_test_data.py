"""
Módulo para inicializar datos de prueba en Firestore y generar videos de prueba.
"""
import os
import uuid
import cv2
import numpy as np
from datetime import datetime
from firebase_admin import firestore, initialize_app, _apps
from config.firestore_schema import validate_document, COLLECTIONS
from typing import Dict, Any

def get_db():
    return firestore.client()

def initialize_firestore():
    """Inicializa la conexión con Firestore."""
    if not os.getenv('FIRESTORE_EMULATOR_HOST'):
        if not _apps:
            initialize_app()
    return firestore.client()

def clear_test_data():
    """Limpia todos los datos de prueba de Firestore."""
    db = initialize_firestore()
    for collection in COLLECTIONS.keys():
        docs = db.collection(collection).where('is_test', '==', True).get()
        for doc in docs:
            doc.reference.delete()

def create_test_users(n=1):
    """Crea n usuarios de prueba en Firestore."""
    db = initialize_firestore()
    users = []
    
    for i in range(n):
        user_id = str(uuid.uuid4())
        user_data = {
            'email': f'test{i}@padelyzer.com',
            'fecha_registro': datetime.now(),
            'nivel': 'principiante',
            'posicion_preferida': 'drive',
            'ultimo_analisis': None,
            'tipo_ultimo_analisis': None,
            'fecha_ultimo_analisis': None,
            'is_test': True
        }
        
        validate_document('users', user_data)
        db.collection('users').document(user_id).set(user_data)
        users.append(user_id)
    
    return users

def create_test_strokes(user_id):
    """Crea golpes de prueba para un usuario."""
    db = initialize_firestore()
    
    strokes_data = {
        'user_id': user_id,
        'timestamp': datetime.now(),
        'strokes': {
            'tipo': 'derecha',
            'confianza': 0.85,
            'calidad': 75.0,
            'max_elbow_angle': 135.0,
            'max_wrist_speed': 15.0,
            'inicio': 1.2,
            'fin': 1.8,
            'posicion_cancha': 'fondo'
        },
        'is_test': True
    }
    
    validate_document('player_strokes', strokes_data)
    db.collection('player_strokes').add(strokes_data)

def create_test_padel_iq_history(user_id):
    """Crea historial de Padel IQ para un usuario."""
    db = initialize_firestore()
    
    history_data = {
        'user_id': user_id,
        'timestamp': datetime.now(),
        'padel_iq': 75.0,
        'tecnica': 80.0,
        'ritmo': 70.0,
        'fuerza': 75.0,
        'tipo_analisis': 'entrenamiento',
        'is_test': True
    }
    
    validate_document('padel_iq_history', history_data)
    db.collection('padel_iq_history').add(history_data)

def create_test_video_analisis(user_id):
    """Crea un análisis de video de prueba."""
    db = initialize_firestore()
    
    # Generar frames de previsualización
    preview_frames = []
    for i in range(5):
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.putText(frame, f'Preview {i}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        preview_frames.append(frame)
    
    analysis_data = {
        'user_id': user_id,
        'video_url': f'test_video_{uuid.uuid4()}.mp4',
        'tipo_video': 'entrenamiento',
        'fecha_analisis': datetime.now(),
        'estado': 'completado',
        'resultados': {
            'padel_iq': 75.0,
            'tecnica': 80.0,
            'ritmo': 70.0,
            'fuerza': 75.0
        },
        'preview_frames': preview_frames,
        'is_test': True
    }
    
    validate_document('video_analisis', analysis_data)
    doc_ref = db.collection('video_analisis').document()
    doc_ref.set(analysis_data)
    return doc_ref.id

def create_test_video(output_path='test_videos', filename='test_video.mp4', resolution=(1280, 720), duration=10, fps=30):
    """Crea un video de prueba con las especificaciones dadas."""
    os.makedirs(output_path, exist_ok=True)
    video_path = os.path.join(output_path, filename)
    
    # Crear video con OpenCV
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, resolution)
    
    for _ in range(duration * fps):
        frame = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)
        # Dibujar algo en el frame para que no esté vacío
        cv2.rectangle(frame, (0, 0), (resolution[0], resolution[1]), (0, 255, 0), 50)
        out.write(frame)
    
    out.release()
    return video_path
"""
Inicialización de datos de prueba para Padelyzer.

Este módulo proporciona funciones y constantes para configurar
el entorno de prueba con datos predeterminados.
"""

import os
import tempfile
import uuid
from datetime import datetime

# URLs y endpoints para pruebas
BASE_URL = "http://localhost:8000/api/v1"
API_VERSION = "v1"

# Datos de usuario de prueba
TEST_USER_EMAIL = f"test_{uuid.uuid4()}@example.com"
TEST_USER_PASSWORD = "Test123!"
TEST_USER_NAME = f"Test User {datetime.now().strftime('%Y%m%d%H%M%S')}"
TEST_USER_LEVEL = "intermedio"
TEST_USER_POSITION = "derecha"

# Ruta del video de prueba
TEST_VIDEO_PATH = os.path.join(os.path.dirname(__file__), "resources", "test_video.mp4")

def create_test_video(size_kb=100):
    """
    Crea un archivo de video temporal para pruebas.
    
    Args:
        size_kb: Tamaño del archivo en KB (por defecto 100KB)
        
    Returns:
        Ruta al archivo temporal creado
    """
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
        # Crear contenido dummy del tamaño especificado
        dummy_content = b"0" * (size_kb * 1024)
        temp_file.write(dummy_content)
        temp_file.flush()
        return temp_file.name

def cleanup_test_files(files):
    """
    Elimina archivos temporales de prueba.
    
    Args:
        files: Lista de rutas de archivos a eliminar
    """
    for file in files:
        try:
            if os.path.exists(file):
                os.unlink(file)
        except Exception as e:
            print(f"Error al limpiar archivo {file}: {str(e)}")
def create_test_videos():
    """Crea videos de prueba para entrenamiento y partido."""
    videos = {
        'entrenamiento': create_test_video(
            filename='test_entrenamiento.mp4',
            resolution=(1280, 720),
            duration=10
        ),
        'partido': create_test_video(
            filename='test_partido.mp4',
            resolution=(1280, 720),
            duration=30
        )
    }
    return videos

def get_test_user_data() -> Dict[str, Any]:
    """Retorna datos de prueba para un usuario."""
    return {
        "id": "test_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True,
        "email_verified": True,
        "preferences": {
            "notifications": True,
            "email_notifications": True,
            "language": "es",
            "timezone": "UTC"
        }
    }

def get_test_video_data() -> Dict[str, Any]:
    """Retorna datos de prueba para un video."""
    return {
        "id": "test_video_123",
        "user_id": "test_user_123",
        "filename": "test_video.mp4",
        "video_type": "training",
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

def get_test_padel_iq_data() -> Dict[str, Any]:
    """Retorna datos de prueba para Padel IQ."""
    return {
        "id": "test_iq_123",
        "user_id": "test_user_123",
        "score": 85,
        "metrics": {
            "technique": 80,
            "tactics": 85,
            "physical": 90
        },
        "created_at": datetime.utcnow()
    } 