import requests
import logging
import os
import cv2
import numpy as np
from datetime import datetime
import tempfile

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración
BASE_URL = 'http://localhost:8082'
TEST_USER = {
    'email': 'test@example.com',
    'password': 'password123'
}

def create_test_video(resolution=(1280, 720), type="entrenamiento"):
    """
    Crea un archivo de video de prueba con las dimensiones especificadas.
    
    Args:
        resolution (tuple): Resolución del video (ancho, alto)
        type (str): Tipo de video ('entrenamiento' o 'partido')
        
    Returns:
        str: Ruta al archivo de video creado
    """
    filename = f"test_{type}_{resolution[0]}x{resolution[1]}.mp4"
    filepath = os.path.join(tempfile.gettempdir(), filename)
    
    # Crear un archivo de video ficticio
    with open(filepath, "wb") as f:
        f.write(b"Mock video data")
    
    return filepath

def create_test_user():
    """
    Crea un usuario de prueba en la base de datos.
    
    Returns:
        dict: Datos del usuario creado
    """
    return {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "name": "Test User",
        "created_at": datetime.utcnow().isoformat()
    }

def create_test_analysis(user_id):
    """
    Crea un análisis de prueba para un usuario.
    
    Args:
        user_id (str): ID del usuario
        
    Returns:
        dict: Datos del análisis creado
    """
    return {
        "analysis_id": "test_analysis_123",
        "user_id": user_id,
        "video_url": "https://example.com/test_video.mp4",
        "created_at": datetime.utcnow().isoformat(),
        "metrics": {
            "padel_iq": 75,
            "technique": 80,
            "rhythm": 70,
            "power": 85
        }
    }

def test_complete_flow():
    """Prueba el flujo completo de la aplicación."""
    try:
        # 1. Crear usuario de prueba
        logger.info("Creando usuario de prueba...")
        response = requests.post(f'{BASE_URL}/signup', json=TEST_USER)
        response.raise_for_status()
        user_data = response.json()
        user_id = user_data['user']['uid']
        logger.info(f"Usuario creado con ID: {user_id}")

        # 2. Iniciar sesión
        logger.info("Iniciando sesión...")
        response = requests.post(f'{BASE_URL}/login', json=TEST_USER)
        response.raise_for_status()
        logger.info("Sesión iniciada correctamente")

        # 3. Crear y subir video de prueba
        logger.info("Creando video de prueba...")
        video_path = create_test_video()
        
        logger.info("Subiendo video...")
        with open(video_path, 'rb') as video_file:
            files = {'video': video_file}
            data = {
                'user_id': user_id,
                'tipo_video': 'entrenamiento'
            }
            response = requests.post(
                f'{BASE_URL}/process_training_video',
                files=files,
                data=data
            )
            response.raise_for_status()
            analysis_data = response.json()
            analysis_id = analysis_data['analysis_id']
            logger.info(f"Video procesado. ID de análisis: {analysis_id}")

        # 4. Obtener detalles del análisis
        logger.info("Obteniendo detalles del análisis...")
        response = requests.get(f'{BASE_URL}/get_analysis/{analysis_id}')
        response.raise_for_status()
        analysis_details = response.json()
        logger.info("Detalles del análisis obtenidos correctamente")

        # 5. Obtener analytics del usuario
        logger.info("Obteniendo analytics del usuario...")
        response = requests.get(f'{BASE_URL}/dashboard/get_user_analytics', params={'user_id': user_id})
        response.raise_for_status()
        analytics = response.json()
        logger.info("Analytics obtenidos correctamente")

        # Limpieza
        logger.info("Realizando limpieza...")
        if os.path.exists(video_path):
            os.remove(video_path)
        logger.info("Limpieza completada")

        return True

    except Exception as e:
        logger.error(f"Error durante la prueba: {str(e)}")
        return False

if __name__ == '__main__':
    logger.info("Iniciando prueba de integración...")
    success = test_complete_flow()
    if success:
        logger.info("¡Prueba completada exitosamente!")
    else:
        logger.error("La prueba falló") 