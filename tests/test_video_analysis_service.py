import pytest
import numpy as np
from app.services.video_analysis_service import VideoAnalysisService
from unittest.mock import Mock, patch

@pytest.fixture
def video_analysis_service():
    return VideoAnalysisService(model_size="n", device="cpu")

@pytest.fixture
def mock_frame():
    return np.zeros((480, 640, 3), dtype=np.uint8)

@pytest.fixture
def mock_player_detection():
    return {
        'id': 1,
        'bbox': [100, 100, 200, 300],
        'wrist_speed': 1.0,
        'elbow_angle': 120,
        'wrist_direction': 0.5
    }

def test_analyze_video(video_analysis_service, mock_frame):
    """Test del análisis completo de video."""
    with patch('app.services.video_processor.VideoProcessor.process_video') as mock_process_video, \
         patch('app.services.player_detector.PlayerDetector.detect_player') as mock_detect_player, \
         patch('app.services.player_detector.PlayerDetector.detect') as mock_detect, \
         patch('app.services.stroke_detector.StrokeDetector.detect_stroke') as mock_detect_stroke:
        
        # Configurar mocks
        mock_process_video.return_value = [mock_frame] * 30  # 1 segundo de video
        mock_detect_player.return_value = {'x': 100, 'y': 100}
        mock_detect.return_value = [mock_player_detection]
        mock_detect_stroke.return_value = True
        
        # Ejecutar análisis
        results = video_analysis_service.analyze_video("test_video.mp4")
        
        # Verificar resultados
        assert results['total_frames'] == 30
        assert results['duration'] == 1.0
        assert 'analysis' in results
        assert 'strokes' in results['analysis']
        assert 'movements' in results['analysis']
        assert 'stroke_types' in results['analysis']
        assert 'player_positions' in results['analysis']

def test_find_active_player(video_analysis_service, mock_frame):
    """Test de la detección del jugador activo."""
    detections = [
        {
            'id': 1,
            'wrist_speed': 1.0,
            'elbow_angle': 120,
            'wrist_direction': 0.5
        },
        {
            'id': 2,
            'wrist_speed': 0.2,
            'elbow_angle': 90,
            'wrist_direction': 0.1
        }
    ]
    
    active_player = video_analysis_service._find_active_player(detections, mock_frame)
    assert active_player is not None
    assert active_player['id'] == 1  # El primer jugador tiene mayor score de movimiento

def test_classify_stroke(video_analysis_service):
    """Test de la clasificación de golpes."""
    # Test smash
    smash_detection = {
        'wrist_speed': 1.5,
        'elbow_angle': 160,
        'wrist_direction': 0.5
    }
    assert video_analysis_service._classify_stroke(smash_detection) == "smash"
    
    # Test bandeja
    bandeja_detection = {
        'wrist_speed': 0.8,
        'elbow_angle': 130,
        'wrist_direction': 0.5
    }
    assert video_analysis_service._classify_stroke(bandeja_detection) == "bandeja"
    
    # Test volea derecha
    volea_detection = {
        'wrist_speed': 0.1,
        'elbow_angle': 80,
        'wrist_direction': 0.5
    }
    assert video_analysis_service._classify_stroke(volea_detection) == "volea_derecha"
    
    # Test volea revés
    volea_reves_detection = {
        'wrist_speed': 0.1,
        'elbow_angle': 80,
        'wrist_direction': -0.5
    }
    assert video_analysis_service._classify_stroke(volea_reves_detection) == "volea_reves"

def test_analyze_stroke_types(video_analysis_service):
    """Test del análisis de tipos de golpes."""
    strokes = [
        {'type': 'smash'},
        {'type': 'smash'},
        {'type': 'bandeja'},
        {'type': 'volea_derecha'},
        {'type': 'volea_reves'}
    ]
    
    stroke_types = video_analysis_service._analyze_stroke_types(strokes)
    assert stroke_types['smash'] == 2
    assert stroke_types['bandeja'] == 1
    assert stroke_types['volea_derecha'] == 1
    assert stroke_types['volea_reves'] == 1 