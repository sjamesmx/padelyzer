import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.padel_iq import PadelIQRequest
import os
import cv2
import numpy as np
import sys

client = TestClient(app)

def create_test_video(filename: str, duration: int = 5, fps: int = 30):
    """Crea un video de prueba válido."""
    # Crear un video con frames negros
    height, width = 480, 640
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    for _ in range(duration * fps):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        out.write(frame)
    
    out.release()

def test_analyze_training_video():
    """Test para el análisis de video de entrenamiento."""
    video_url = "https://firebasestorage.googleapis.com/v0/b/pdzr-458820.firebasestorage.app/o/lety.mp4?alt=media&token=4e7c5d33-423b-4d0d-8b6f-5699d6604296"
    response = client.post(
        "/api/v1/padel-iq/calculate",
        json={
            "user_id": "test_user",
            "video_url": video_url,
            "tipo_video": "entrenamiento",
            "player_position": {"side": "right", "zone": "back"}
        }
    )
    print("Status:", response.status_code)
    print("Body:", response.text)
    assert False, response.text
    sys.stdout.flush()
    assert response.status_code == 200
    result = response.json()
    assert "analysis_id" in result
    assert "task_id" in result
    assert result["status"] == "processing"
    print(result)

def test_analyze_game_video():
    """Test para el análisis de video de juego."""
    video_url = "https://firebasestorage.googleapis.com/v0/b/pdzr-458820.firebasestorage.app/o/lety.mp4?alt=media&token=4e7c5d33-423b-4d0d-8b6f-5699d6604296"
    response = client.post(
        "/api/v1/padel-iq/calculate",
        json={
            "user_id": "test_user",
            "video_url": video_url,
            "tipo_video": "juego",
            "player_position": {"side": "right", "zone": "back"}
        }
    )
    print("Status:", response.status_code)
    print("Body:", response.text)
    assert False, response.text
    sys.stdout.flush()
    assert response.status_code == 200
    result = response.json()
    assert "analysis_id" in result
    assert "task_id" in result
    assert result["status"] == "processing"
    print(result)

def test_get_user_history():
    """Test para obtener el historial de análisis de un usuario."""
    user_id = "test_user_123"
    response = client.get(f"/api/v1/padel-iq/history/{user_id}")
    assert response.status_code == 200
    result = response.json()
    assert "history" in result
    assert isinstance(result["history"], list)

def test_video_processing_flow():
    """Test para el flujo completo de procesamiento de video."""
    from app.services.video_processor import VideoProcessor
    from app.services.player_detector import PlayerDetector
    
    processor = VideoProcessor()
    detector = PlayerDetector()
    
    # Crear un video de prueba válido
    video_url = "test_video.mp4"
    create_test_video(video_url)
    
    try:
        frames = processor.process_video(video_url)
        assert len(frames) > 0
        
        position = detector.detect_player(frames[0])
        assert isinstance(position, dict)
        assert "side" in position
        assert "zone" in position
    finally:
        if os.path.exists(video_url):
            os.remove(video_url)

def test_error_handling():
    """Test para el manejo de errores."""
    # Test con datos inválidos
    data = {
        "user_id": "test_user_123",
        "video_url": "invalid_url",
        "tipo_video": "invalid_type"
    }
    
    response = client.post("/api/v1/padel-iq/calculate", json=data)
    print("Status:", response.status_code)
    print("Body:", response.text)
    assert False, response.text
    sys.stdout.flush()
    assert response.status_code == 422  # Unprocessable Entity
    
    # Test con video inexistente
    data = {
        "user_id": "test_user_123",
        "video_url": "https://example.com/nonexistent.mp4",
        "tipo_video": "entrenamiento"
    }
    
    response = client.post("/api/v1/padel-iq/calculate", json=data)
    print("Status:", response.status_code)
    print("Body:", response.text)
    assert False, response.text
    sys.stdout.flush()
    assert response.status_code == 500  # Internal Server Error

# Test para verificar el error 422
def test_error_handling_422():
    response = client.post(
        "/api/v1/padel-iq/calculate",
        json={
            "user_id": "test_user",
            "video_url": "https://firebasestorage.googleapis.com/v0/b/pdzr-458820.firebasestorage.app/o/lety.mp4?alt=media&token=4e7c5d33-423b-4d0d-8b6f-5699d6604296",
            "tipo_video": "entrenamiento",
            "player_position": {"side": "right", "zone": "back"}
        }
    )
    print("Status:", response.status_code)
    print("Body:", response.text)
    assert False, response.text
    sys.stdout.flush()
    assert response.status_code == 422  # Unprocessable Entity

# Test para verificar el error 500
def test_error_handling_500():
    response = client.post(
        "/api/v1/padel-iq/calculate",
        json={
            "user_id": "test_user",
            "video_url": "https://example.com/nonexistent.mp4",
            "tipo_video": "entrenamiento"
        }
    )
    print("Status:", response.status_code)
    print("Body:", response.text)
    assert False, response.text
    sys.stdout.flush()
    assert response.status_code == 500  # Internal Server Error 