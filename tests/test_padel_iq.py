import pytest
from services.padel_iq_calculator import calculate_padel_iq_granular
from services.analysis_manager import AnalysisManager
from services.video_processor import VideoProcessor
from services.player_detector import PlayerDetector
import numpy as np

@pytest.mark.unit
def test_calculate_padel_iq_granular():
    """Test para el cálculo granular del Padel IQ."""
    # Test caso básico
    result = calculate_padel_iq_granular(
        max_elbow_angle=90,
        max_wrist_speed=10,
        tipo='training'
    )
    
    assert 'tecnica' in result
    assert 'fuerza' in result
    assert 'ritmo' in result
    assert 'repeticion' in result
    assert 'padel_iq' in result
    assert 0 <= result['padel_iq'] <= 100

    # Test caso extremo
    result = calculate_padel_iq_granular(
        max_elbow_angle=180,
        max_wrist_speed=30,
        tipo='training'
    )
    
    assert result['padel_iq'] <= 100

    # Test caso de juego
    result = calculate_padel_iq_granular(
        max_elbow_angle=90,
        max_wrist_speed=15,
        tipo='game'
    )
    
    assert result['padel_iq'] <= 100
    assert result['padel_iq'] > 0

@pytest.mark.unit
def test_analysis_manager(firebase_app, mock_video, mock_player_position):
    """Test para el gestor de análisis."""
    manager = AnalysisManager()
    
    # Test análisis de entrenamiento
    result = manager.analyze_training_video(
        video_url=mock_video['url'],
        player_position=mock_player_position
    )
    
    assert 'padel_iq' in result
    assert 'metrics' in result
    assert 'strokes' in result
    
    # Validar estructura del Padel IQ
    assert isinstance(result['padel_iq'], dict)
    assert 'tecnica' in result['padel_iq']
    assert 'fuerza' in result['padel_iq']
    assert 'ritmo' in result['padel_iq']
    assert 'repeticion' in result['padel_iq']
    assert 'padel_iq' in result['padel_iq']
    
    # Validar métricas por defecto cuando no hay golpes
    assert result['padel_iq']['padel_iq'] == 0
    assert result['padel_iq']['tecnica'] == 0
    assert result['padel_iq']['fuerza'] == 0
    assert result['padel_iq']['ritmo'] == 0
    assert result['padel_iq']['repeticion'] == 0
    
    assert result['metrics']['total_strokes'] == 0
    assert result['metrics']['max_elbow_angle'] == 0
    assert result['metrics']['max_wrist_speed'] == 0
    assert result['metrics']['avg_stroke_interval'] == 0
    assert result['metrics']['stroke_types'] == {}
    
    assert result['strokes'] == []

    # Test análisis de juego
    result = manager.analyze_game_video(
        video_url=mock_video['url'],
        player_position=mock_player_position
    )
    
    assert 'padel_iq' in result
    assert 'metrics' in result
    assert 'game_data' in result
    
    # Validar estructura del Padel IQ
    assert isinstance(result['padel_iq'], dict)
    assert 'tecnica' in result['padel_iq']
    assert 'fuerza' in result['padel_iq']
    assert 'ritmo' in result['padel_iq']
    assert 'repeticion' in result['padel_iq']
    assert 'padel_iq' in result['padel_iq']
    
    # Validar métricas por defecto cuando no hay golpes
    assert result['padel_iq']['padel_iq'] == 0
    assert result['padel_iq']['tecnica'] == 0
    assert result['padel_iq']['fuerza'] == 0
    assert result['padel_iq']['ritmo'] == 0
    assert result['padel_iq']['repeticion'] == 0
    
    assert result['metrics']['total_points'] == 0
    assert result['metrics']['points_won'] == 0
    assert result['metrics']['net_effectiveness'] == 0
    assert result['metrics']['court_coverage'] == 0
    assert result['metrics']['max_elbow_angle'] == 0
    assert result['metrics']['max_wrist_speed'] == 0

@pytest.mark.unit
def test_video_processor(mock_video, mock_player_position):
    """Test para el procesador de video."""
    processor = VideoProcessor()
    
    # Test procesamiento de video
    frames = processor.process_video(mock_video['url'])
    assert len(frames) > 0
    
    # Test análisis de golpes
    strokes = processor.analyze_strokes(
        frames,
        player_position=mock_player_position
    )
    assert isinstance(strokes, list)

@pytest.mark.unit
def test_player_detector(mock_video):
    """Test para el detector de jugadores."""
    detector = PlayerDetector()
    processor = VideoProcessor()
    frames = processor.process_video(mock_video['url'])
    
    # Test detección de jugador
    position = detector.detect_player(frames[0])
    assert 'x' in position
    assert 'y' in position
    assert 'width' in position
    assert 'height' in position
    assert 'keypoints' in position

@pytest.mark.unit
def test_normalization():
    """Test para la normalización de métricas."""
    # Test normalización de ángulo de codo
    result = calculate_padel_iq_granular(
        max_elbow_angle=0,
        max_wrist_speed=10,
        tipo='training'
    )
    assert result['tecnica'] <= 100

    result = calculate_padel_iq_granular(
        max_elbow_angle=180,
        max_wrist_speed=10,
        tipo='training'
    )
    assert result['tecnica'] <= 100

    # Test normalización de velocidad de muñeca
    result = calculate_padel_iq_granular(
        max_elbow_angle=90,
        max_wrist_speed=0,
        tipo='training'
    )
    assert result['fuerza'] <= 100

    result = calculate_padel_iq_granular(
        max_elbow_angle=90,
        max_wrist_speed=30,
        tipo='training'
    )
    assert result['fuerza'] <= 100

@pytest.mark.integration
def test_full_analysis_flow(firebase_app, mock_video, mock_player_position):
    """Test de integración para el flujo completo de análisis."""
    manager = AnalysisManager()
    processor = VideoProcessor()
    detector = PlayerDetector()

    # Procesar video
    frames = processor.process_video(mock_video['url'])
    assert len(frames) > 0

    # Detectar jugador
    position = detector.detect_player(frames[0])
    assert all(k in position for k in ['x', 'y', 'width', 'height'])

    # Analizar video
    result = manager.analyze_training_video(
        video_url=mock_video['url'],
        player_position=position
    )
    
    assert 'padel_iq' in result
    assert 'metrics' in result
    assert 'strokes' in result
    
    # Validar estructura del Padel IQ
    assert isinstance(result['padel_iq'], dict)
    assert 'tecnica' in result['padel_iq']
    assert 'fuerza' in result['padel_iq']
    assert 'ritmo' in result['padel_iq']
    assert 'repeticion' in result['padel_iq']
    assert 'padel_iq' in result['padel_iq']
    
    # Validar métricas por defecto cuando no hay golpes
    assert result['padel_iq']['padel_iq'] == 0
    assert result['padel_iq']['tecnica'] == 0
    assert result['padel_iq']['fuerza'] == 0
    assert result['padel_iq']['ritmo'] == 0
    assert result['padel_iq']['repeticion'] == 0
    
    assert result['metrics']['total_strokes'] == 0
    assert result['metrics']['max_elbow_angle'] == 0
    assert result['metrics']['max_wrist_speed'] == 0
    assert result['metrics']['avg_stroke_interval'] == 0
    assert result['metrics']['stroke_types'] == {}
    
    assert result['strokes'] == []

    # Verificar métricas específicas
    metrics = result['metrics']
    assert 'total_strokes' in metrics
    assert 'stroke_types' in metrics
    assert 'max_elbow_angle' in metrics
    assert 'max_wrist_speed' in metrics
    assert 'avg_stroke_interval' in metrics 