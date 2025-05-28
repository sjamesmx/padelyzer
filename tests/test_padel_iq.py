import pytest
from app.services.padel_iq_calculator import calculate_padel_iq_granular
from app.services.analysis_manager import AnalysisManager
from app.services.video_processor import VideoProcessor
from app.services.player_detector import PlayerDetector
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
import os
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

client = TestClient(app)

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
def test_analysis_manager(mock_video):
    with patch('app.services.video_processor.VideoProcessor.process_video') as mock_process_video:
        mock_frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(10)]
        mock_process_video.return_value = mock_frames
        manager = AnalysisManager()
        result = manager.analyze_training_video(
            video_url=mock_video,
            player_position={"side": "right", "zone": "back"}
        )
        assert result is not None
        assert "padel_iq" in result
        assert "metrics" in result

@pytest.mark.unit
def test_video_processor(mock_video):
    with patch('app.services.video_processor.VideoProcessor.process_video') as mock_process_video:
        mock_frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(10)]
        mock_process_video.return_value = mock_frames
        processor = VideoProcessor()
        frames = processor.process_video(mock_video)
        assert frames is not None
        assert len(frames) > 0

@pytest.mark.unit
def test_player_detector(mock_video):
    with patch('app.services.video_processor.VideoProcessor.process_video') as mock_process_video:
        mock_frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(10)]
        mock_process_video.return_value = mock_frames
        
        detector = PlayerDetector()
        detector.initialize("cpu")
        position = detector.detect_player(mock_frames[0])
        
        assert isinstance(position, dict)
        assert "x" in position
        assert "y" in position
        assert "width" in position
        assert "height" in position
        assert "keypoints" in position
        assert "side" in position
        assert "zone" in position
        assert position["side"] in ["left", "right"]
        assert position["zone"] in ["net", "back"]

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
def test_full_analysis_flow(mock_video):
    with patch('app.services.video_processor.VideoProcessor.process_video') as mock_process_video:
        mock_frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(10)]
        mock_process_video.return_value = mock_frames
        
        detector = PlayerDetector()
        detector.initialize("cpu")
        position = detector.detect_player(mock_frames[0])
        
        assert isinstance(position, dict)
        assert "x" in position
        assert "y" in position
        assert "width" in position
        assert "height" in position
        assert "keypoints" in position
        assert "side" in position
        assert "zone" in position
        assert position["side"] in ["left", "right"]
        assert position["zone"] in ["net", "back"]

@pytest.fixture
def test_video_path():
    # Asegurarse de que el directorio de videos existe
    os.makedirs("videos", exist_ok=True)
    # Crear un archivo de video de prueba
    video_path = "videos/test_training.mp4"
    with open(video_path, "wb") as f:
        f.write(b"fake video content")
    return video_path

@pytest.mark.asyncio
async def test_calculate_padel_iq_training(mock_firestore, mock_firebase_init, client):
    # Preparar los datos de la petición
    request_data = {
        "user_id": "test_user_123",
        "video_url": "file:///Users/ja/padelyzer/videos/test_training.mp4",
        "tipo_video": "entrenamiento",
        "player_position": None,
        "game_splits": None
    }

    # Realizar la petición POST
    response = client.post("/api/v1/padel-iq/calculate", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    analysis_id = data["analysis_id"]

    # Consultar el estado del análisis
    status_response = client.get(f"/api/v1/padel-iq/status/{analysis_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["status"] == "completed"
    assert "padel_iq" in status_data
    assert "metrics" in status_data 