"""
Configuración de pytest para Padelyzer.
"""
import os
import sys

# Agregar el directorio backend al PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from firebase_admin import firestore, initialize_app, delete_app, _apps, get_app, credentials
from fastapi.testclient import TestClient
from app.main import app
from app.config.firebase import initialize_firebase
import firebase_admin

# Initialize Firebase for tests
initialize_firebase()

@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)

@pytest.fixture(scope="session")
def firestore_client():
    """Get a real Firestore client for integration tests."""
    return firestore.client()

@pytest.fixture(scope='session')
def firebase_app():
    """Fixture para inicializar Firebase una sola vez durante las pruebas."""
    try:
        app = firebase_admin.initialize_app()
    except ValueError:
        # Si ya existe una app, obtener la existente
        app = firebase_admin.get_app()
    return app

@pytest.fixture
def mock_video():
    """Fixture para simular un video de prueba."""
    return {
        'url': 'tests/test_videos/test_video.mp4',
        'duration': 5,
        'resolution': (640, 480),
        'size': os.path.getsize('tests/test_videos/test_video.mp4')
    }

@pytest.fixture
def mock_player_position():
    """Fixture para simular la posición del jugador."""
    return {
        'x': 0,
        'y': 0,
        'width': 100,
        'height': 200,
        'keypoints': []
    } 