"""
Configuración de pytest para Padelyzer.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta, UTC
import jwt
from app.core.config import settings
import firebase_admin
from firebase_admin import credentials, firestore

# Configurar variables de entorno para pruebas
os.environ["FIREBASE_PROJECT_ID"] = "test-project"
os.environ["FIREBASE_PRIVATE_KEY_ID"] = "test-key-id"
os.environ["FIREBASE_PRIVATE_KEY"] = "test-key"
os.environ["FIREBASE_CLIENT_EMAIL"] = "test@example.com"
os.environ["FIREBASE_CLIENT_ID"] = "test-client-id"
os.environ["FIREBASE_CLIENT_CERT_URL"] = "https://test.example.com/cert"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

# Agregar el directorio backend al PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI application."""
    from app.main import app
    return TestClient(app)

@pytest.fixture(scope="session")
def mock_firebase():
    """Mock de Firebase Admin para pruebas."""
    # Mock de Firebase Admin
    mock_app = MagicMock()
    mock_cred = MagicMock()
    
    # Configurar el mock para que no intente conexiones reales
    with patch('firebase_admin.initialize_app', return_value=mock_app) as mock_init:
        with patch('firebase_admin.credentials.Certificate', return_value=mock_cred):
            # Inicializar Firebase Admin con el mock
            if not firebase_admin._apps:
                firebase_admin.initialize_app(mock_cred)
            
            # Crear mock de Firestore
            mock_db = MagicMock()
            mock_collection = MagicMock()
            mock_document = MagicMock()
            mock_query = MagicMock()
            
            # Configurar el mock para simular operaciones de Firestore
            mock_db.collection.return_value = mock_collection
            mock_collection.document.return_value = mock_document
            mock_collection.where.return_value = mock_query
            mock_query.get.return_value = []
            
            # Mock de documentos con respuestas inmediatas
            mock_document.get.return_value = MagicMock(exists=False)
            mock_document.set.return_value = None
            mock_document.update.return_value = None
            mock_document.delete.return_value = None
            
            # Configurar el mock para que no intente conexiones reales
            mock_db._client = MagicMock()
            mock_db._client._credentials = MagicMock()
            mock_db._client._credentials.before_request = MagicMock()
            
            # Reemplazar el cliente de Firestore con nuestro mock
            with patch('firebase_admin.firestore.client', return_value=mock_db):
                yield mock_db

@pytest.fixture(scope="session")
def test_user():
    """Test user data."""
    return {
        "id": "test123",
        "email": "test@example.com",
        "password": "Test123!",
        "username": "testuser",
        "full_name": "Test User",
        "created_at": "2024-03-20T00:00:00Z",
        "updated_at": "2024-03-20T00:00:00Z"
    }

@pytest.fixture(scope="session")
def test_video():
    """Test video data."""
    return {
        "id": "video123",
        "user_id": "test123",
        "title": "Test Video",
        "description": "Test Description",
        "url": "https://example.com/video.mp4",
        "thumbnail_url": "https://example.com/thumbnail.jpg",
        "duration": 120,
        "created_at": "2024-03-20T00:00:00Z",
        "updated_at": "2024-03-20T00:00:00Z"
    }

@pytest.fixture(scope="session")
def test_match():
    """Test match data."""
    return {
        "id": "match123",
        "user_id": "test123",
        "partner_id": "partner123",
        "status": "pending",
        "created_at": "2024-03-20T00:00:00Z",
        "updated_at": "2024-03-20T00:00:00Z"
    }

@pytest.fixture(scope="session")
def test_token(test_user):
    """Generate a test JWT token."""
    token_data = {
        "sub": test_user["email"],
        "exp": datetime.now(UTC) + timedelta(minutes=30)
    }
    return jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

@pytest.fixture(scope="session")
def auth_headers(test_token):
    """Return headers with authentication token."""
    return {"Authorization": f"Bearer {test_token}"}

@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)

@pytest.fixture(scope="session")
def firestore_client():
    """Get a real Firestore client for integration tests."""
    return firestore.client()

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