import requests
import logging
import json
from datetime import datetime
import os
import sys
import uuid

# Agregar el directorio padre al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from create_test_video import create_test_video
from init_test_db import init_test_data
from config.mock_firebase import client

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
BASE_URL = 'http://localhost:8000'  # Updated to match FastAPI port

def test_complete_flow():
    """Prueba el flujo completo del sistema."""
    try:
        # 1. Registrar usuario
        random_email = f"test-{uuid.uuid4()}@example.com"
        user_data = {
            "email": random_email,
            "password": "Test123!",
            "name": "Test User",
            "nivel": "intermedio",
            "posicion_preferida": "derecha"
        }
        
        response = requests.post(
            f'{BASE_URL}/api/v1/auth/signup',
            json=user_data
        )
        
        if response.status_code != 200:
            logger.error(f"Error al registrar usuario: {response.text}")
            return
            
        signup_result = response.json()
        verification_token = signup_result.get('verification_token')
        user_id = signup_result.get('id')
        
        if not verification_token:
            logger.error("No se recibió token de verificación")
            logger.error(f"Respuesta completa del registro: {signup_result}")
            return
            
        logger.info(f"Usuario registrado. ID: {user_id}")
        logger.info(f"Token de verificación: {verification_token}")
        
        # 2. Verificar email
        logger.info("Verificando email...")
        verify_data = {
            "token": verification_token
        }
        
        response = requests.post(
            f'{BASE_URL}/api/v1/auth/verify-email',
            json=verify_data
        )
        
        if response.status_code != 200:
            logger.error(f"Error al verificar email: {response.text}")
            return
            
        logger.info("Email verificado exitosamente")
        
        # 3. Login para obtener token de acceso
        logger.info("Iniciando sesión...")
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        
        response = requests.post(
            f'{BASE_URL}/api/v1/auth/login',
            data=login_data
        )
        
        if response.status_code != 200:
            logger.error(f"Error al iniciar sesión: {response.text}")
            return
            
        login_result = response.json()
        access_token = login_result.get('access_token')
        
        if not access_token:
            logger.error("No se recibió token de acceso")
            return
            
        logger.info("Sesión iniciada exitosamente")
        
        # 4. Crear video de prueba
        logger.info("Creando video de prueba...")
        video_path = create_test_video()
        
        # 5. Procesar video de entrenamiento
        logger.info("Procesando video de entrenamiento...")
        video_data = {
            'video_url': f'file://{os.path.abspath(video_path)}',
            'user_id': user_id,
            'tipo_video': 'entrenamiento'
        }
        
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.post(
            f'{BASE_URL}/api/v1/videos/process',
            json=video_data,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Error al procesar video: {response.text}")
            return
            
        process_result = response.json()
        analysis_id = process_result.get('analysis_id')
        logger.info(f"Video procesado. ID del análisis: {analysis_id}")
        
        # 6. Obtener detalles del análisis
        logger.info("Obteniendo detalles del análisis...")
        response = requests.get(
            f'{BASE_URL}/api/v1/analysis/{analysis_id}',
            headers=headers
        )
        
        if response.status_code == 200:
            analysis_details = response.json()
            logger.info("Detalles del análisis obtenidos exitosamente")
            logger.debug(json.dumps(analysis_details, indent=2))
        else:
            logger.error(f"Error al obtener detalles del análisis: {response.text}")
        
        # 7. Obtener estadísticas del usuario
        logger.info("Obteniendo estadísticas del usuario...")
        response = requests.get(
            f'{BASE_URL}/api/v1/users/{user_id}/analytics',
            headers=headers
        )
        
        if response.status_code == 200:
            user_analytics = response.json()
            logger.info("Estadísticas del usuario obtenidas exitosamente")
            logger.debug(json.dumps(user_analytics, indent=2))
        else:
            logger.error(f"Error al obtener estadísticas del usuario: {response.text}")
        
        # 8. Limpiar archivos temporales
        if os.path.exists(video_path):
            os.remove(video_path)
            logger.info("Archivos temporales eliminados")
        
        return {
            'success': True,
            'user_id': user_id,
            'analysis_id': analysis_id,
            'access_token': access_token,
            'video_path': video_path
        }
        
    except Exception as e:
        logger.error(f"Error durante la prueba del flujo: {str(e)}")
        raise e

if __name__ == '__main__':
    logger.info("Iniciando prueba del flujo completo...")
    result = test_complete_flow()
    if result and result.get('success'):
        logger.info("Prueba del flujo completada exitosamente")
        logger.info(f"Resultados: {json.dumps(result, indent=2)}")
    else:
        logger.error("La prueba del flujo falló") 