from datetime import datetime
import logging
import sys
import os

# Agregar el directorio padre al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.mock_firebase import initialize_firebase, client

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_test_data():
    """Inicializa la base de datos de prueba con usuarios y datos de ejemplo."""
    try:
        # Inicializar Firebase Mock
        initialize_firebase()
        db = client()
        
        # Crear usuario de prueba
        test_user = {
            'email': 'test@example.com',
            'nombre': 'Usuario Test',
            'fecha_registro': datetime.now(),
            'nivel': 'intermedio',
            'posicion_preferida': 'drive',
            'ultimo_analisis': None,
            'tipo_ultimo_analisis': None,
            'fecha_ultimo_analisis': None
        }
        
        # Guardar usuario en Firestore Mock
        user_ref = db.collection('users').document('test_user_1')
        user_ref.set(test_user)
        logger.info(f"Usuario de prueba creado: {test_user['email']}")

        # Crear algunos análisis de ejemplo
        analisis_ejemplo = {
            'user_id': 'test_user_1',
            'tipo_video': 'entrenamiento',
            'video_url': 'https://storage.googleapis.com/padel-videos/example_training.mp4',
            'fecha_analisis': datetime.now(),
            'estado': 'completado',
            'resultados': {
                'golpes_clasificados': {
                    'derecha': [
                        {
                            'tipo': 'derecha',
                            'confianza': 0.85,
                            'calidad': 75,
                            'max_elbow_angle': 135,
                            'max_wrist_speed': 15,
                            'inicio': 1.2,
                            'fin': 1.8,
                            'posicion_cancha': 'fondo'
                        }
                    ],
                    'reves': [
                        {
                            'tipo': 'reves',
                            'confianza': 0.78,
                            'calidad': 70,
                            'max_elbow_angle': 120,
                            'max_wrist_speed': 12,
                            'inicio': 3.5,
                            'fin': 4.1,
                            'posicion_cancha': 'red'
                        }
                    ]
                },
                'video_duration': 10.5,
                'tipo_analisis': 'entrenamiento'
            }
        }
        
        # Guardar análisis en Firestore Mock
        analisis_ref = db.collection('video_analisis').document()
        analisis_ref.set(analisis_ejemplo)
        
        # Actualizar usuario con el ID del análisis
        user_ref.update({
            'ultimo_analisis': analisis_ref.id,
            'tipo_ultimo_analisis': 'entrenamiento',
            'fecha_ultimo_analisis': datetime.now()
        })
        
        logger.info(f"Análisis de ejemplo creado con ID: {analisis_ref.id}")
        
        return {
            'user_id': 'test_user_1',
            'analysis_id': analisis_ref.id
        }

    except Exception as e:
        logger.error(f"Error al inicializar datos de prueba: {str(e)}")
        raise e

if __name__ == '__main__':
    logger.info("Iniciando inicialización de datos de prueba...")
    result = init_test_data()
    logger.info(f"Datos de prueba inicializados exitosamente: {result}") 