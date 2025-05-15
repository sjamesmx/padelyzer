import pytest
from fastapi.testclient import TestClient
from main import app
from services.analysis_manager import AnalysisManager
from services.video_processor import VideoProcessor
from services.player_detector import PlayerDetector
import os

client = TestClient(app)

def test_analyze_training_video():
    """Test de integración para análisis de video de entrenamiento."""
    # Preparar datos de prueba
    video_url = "test_video.mp4"
    player_position = {
        "x": 0,
        "y": 0,
        "width": 100,
        "height": 200
    }

    # Llamar al endpoint
    response = client.post(
        "/api/v1/padel-iq/analyze/training",
        json={
            "video_url": video_url,
            "player_position": player_position
        }
    )

    # Verificar respuesta
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "processing"

    # Verificar estado de la tarea
    task_id = data["task_id"]
    response = client.get(f"/api/v1/padel-iq/status/{task_id}")
    assert response.status_code == 200

def test_analyze_game_video():
    """Test de integración para análisis de video de juego."""
    # Preparar datos de prueba
    video_url = "test_game.mp4"
    player_position = {
        "x": 0,
        "y": 0,
        "width": 100,
        "height": 200
    }

    # Llamar al endpoint
    response = client.post(
        "/api/v1/padel-iq/analyze/game",
        json={
            "video_url": video_url,
            "player_position": player_position
        }
    )

    # Verificar respuesta
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "processing"

    # Verificar estado de la tarea
    task_id = data["task_id"]
    response = client.get(f"/api/v1/padel-iq/status/{task_id}")
    assert response.status_code == 200

def test_get_user_history():
    """Test de integración para obtener historial de usuario."""
    # Llamar al endpoint
    response = client.get("/api/v1/padel-iq/history/test_user")

    # Verificar respuesta
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert isinstance(data["history"], list)

def test_video_processing_flow():
    """Test de integración para el flujo completo de procesamiento de video."""
    # Inicializar componentes
    manager = AnalysisManager()
    processor = VideoProcessor()
    detector = PlayerDetector()

    # Procesar video
    video_url = "test_video.mp4"
    frames = processor.process_video(video_url)
    assert len(frames) > 0

    # Detectar jugador
    player_position = detector.detect_player(frames[0])
    assert "x" in player_position
    assert "y" in player_position

    # Analizar video
    result = manager.analyze_training_video(video_url, player_position)
    assert "padel_iq" in result
    assert "metrics" in result
    assert "strokes" in result

def test_error_handling():
    """Test de integración para manejo de errores."""
    # Test video inválido
    response = client.post(
        "/api/v1/padel-iq/analyze/training",
        json={
            "video_url": "invalid_video.mp4"
        }
    )
    assert response.status_code == 500

    # Test task_id inválido
    response = client.get("/api/v1/padel-iq/status/invalid_task_id")
    assert response.status_code == 500

    # Test usuario inválido
    response = client.get("/api/v1/padel-iq/history/invalid_user")
    assert response.status_code == 500 