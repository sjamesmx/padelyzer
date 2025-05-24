"""
Pruebas unitarias para VideoProcessor.
"""
import pytest
import cv2
import numpy as np
from app.services.video_processor import VideoProcessor
import tempfile
import os

@pytest.fixture
def video_processor():
    """Fixture para obtener una instancia de VideoProcessor."""
    return VideoProcessor()

@pytest.fixture
def test_video():
    """Fixture para crear un video de prueba temporal."""
    # Crear un video temporal para las pruebas
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
        filename = f.name

    # Crear un video con frames negros
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(filename, fourcc, 30, (640, 480))

    # 30 frames (1 segundo) de un video negro
    for _ in range(30):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        writer.write(frame)

    writer.release()

    yield filename

    # Limpiar después de la prueba
    if os.path.exists(filename):
        os.remove(filename)

def test_preprocess_frame(video_processor):
    """Prueba el preprocesamiento de frames."""
    # Crear un frame de prueba
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 128

    # Procesar el frame
    processed = video_processor._preprocess_frame(frame)

    # Verificar que el resultado es un array numpy
    assert isinstance(processed, np.ndarray)

    # Verificar que el frame procesado es una imagen en escala de grises
    assert len(processed.shape) == 2
    assert processed.shape == (480, 640)

def test_process_batch(video_processor):
    """Prueba el procesamiento por lotes de frames."""
    # Crear un lote de frames de prueba
    batch = [np.ones((480, 640, 3), dtype=np.uint8) * 128 for _ in range(5)]

    # Procesar el lote
    processed_batch = video_processor._process_batch(batch)

    # Verificar que se procesaron todos los frames
    assert len(processed_batch) == len(batch)

    # Verificar que cada frame procesado es una imagen en escala de grises
    for processed in processed_batch:
        assert isinstance(processed, np.ndarray)
        assert len(processed.shape) == 2
        assert processed.shape == (480, 640)

def test_process_video(video_processor, test_video):
    """Prueba el procesamiento de un video completo."""
    # Procesar el video
    frames = video_processor.process_video(test_video)

    # Verificar que se retornan frames
    assert len(frames) > 0

    # Verificar que los frames son arrays numpy
    for frame in frames:
        assert isinstance(frame, np.ndarray)

def test_detect_movement(video_processor):
    """Prueba la detección de movimiento."""
    # Crear frames de prueba
    current_frame = np.ones((480, 640, 3), dtype=np.uint8) * 128

    # Crear un frame previo ligeramente diferente para simular movimiento
    prev_frame = np.ones((480, 640, 3), dtype=np.uint8) * 100

    # Posición del jugador de prueba
    player_position = {'x': 100, 'y': 100, 'width': 50, 'height': 100}

    # Detectar movimiento
    result = video_processor._detect_movement(current_frame, player_position, prev_frame)

    # Verificar la estructura del resultado
    assert 'is_stroke' in result
    assert 'stroke_type' in result
    assert 'elbow_angle' in result
    assert 'wrist_speed' in result

    # La diferencia debería detectar movimiento
    assert result['is_stroke'] is True

def test_analyze_strokes(video_processor):
    """Prueba el análisis de golpes."""
    # Crear frames de prueba - 10 frames con pequeñas diferencias
    frames = []
    for i in range(10):
        # Variar la intensidad para simular movimiento
        frame = np.ones((480, 640, 3), dtype=np.uint8) * (100 + i * 10)
        frames.append(frame)

    # Posición del jugador
    player_position = {'x': 100, 'y': 100, 'width': 50, 'height': 100}

    # Analizar golpes
    strokes = video_processor.analyze_strokes(frames, player_position)

    # Verificar que se devuelve una lista
    assert isinstance(strokes, list)

def test_analyze_game(video_processor):
    """Prueba el análisis de un juego completo."""
    # Crear frames de prueba
    frames = [np.ones((480, 640, 3), dtype=np.uint8) * 128 for _ in range(10)]

    # Posición del jugador
    player_position = {'x': 100, 'y': 100, 'width': 50, 'height': 100}

    # Analizar juego
    result = video_processor.analyze_game(frames, player_position)

    # Verificar la estructura del resultado
    assert 'total_points' in result
    assert 'points_won' in result
    assert 'net_effectiveness' in result
    assert 'court_coverage' in result
    assert 'max_elbow_angle' in result
    assert 'max_wrist_speed' in result
    assert 'strokes' in result
