"""
Pruebas para los servicios básicos de la aplicación.
"""
import pytest
from unittest.mock import patch, MagicMock

def test_service_imports():
    """Test que podemos importar correctamente los servicios."""
    try:
        from app.services import firebase
        assert hasattr(firebase, 'get_firebase_client')
    except ImportError as e:
        pytest.fail(f"Error importando módulo de servicios: {e}")

@pytest.mark.skip("Prueba de integración para ejecutar manualmente")
def test_video_processor_integration():
    """Test de integración para el procesador de video."""
    from app.services.video_processor import VideoProcessor
    import numpy as np

    # Crear instancia del procesador
    processor = VideoProcessor()

    # Crear frames de prueba
    frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(5)]
    player_position = {'x': 100, 'y': 100, 'width': 50, 'height': 100}

    # Analizar frames
    result = processor.analyze_game(frames, player_position)

    # Verificar estructura del resultado
    assert 'strokes' in result
    assert 'total_points' in result
    assert 'points_won' in result
    assert isinstance(result['strokes'], list)

@patch('app.services.firebase.initialize_firebase')
def test_firebase_service(mock_initialize):
    """Test del servicio de Firebase."""
    from app.services import firebase

    # Configurar el mock
    mock_db = MagicMock()
    mock_initialize.return_value = mock_db

    # Llamar a la función
    client = firebase.get_firebase_client()

    # Verificar que se llamó a initialize_firebase
    mock_initialize.assert_called_once()

    # Verificar que se retornó el cliente correcto
    assert client == mock_db
