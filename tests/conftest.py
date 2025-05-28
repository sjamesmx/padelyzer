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
from google.cloud import firestore

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

@pytest.fixture(autouse=True)
def mock_firebase_init():
    """Mock Firebase initialization for all tests."""
    with patch('firebase_admin.initialize_app') as mock_init:
        with patch('firebase_admin.get_app') as mock_get_app:
            mock_app = MagicMock()
            mock_get_app.return_value = mock_app
            yield mock_app

@pytest.fixture(autouse=True)
def mock_firestore():
    """Mock global de Firestore para todos los tests."""
    mock_db = MagicMock()

    # Datos de prueba coherentes
    test_data = {
        'user_id': 'test_user_123',
        'video_url': 'file:///app/videos/test.mp4',
        'video_type': 'entrenamiento',
        'player_position': {'side': 'left', 'zone': 'back'},
        'status': 'completed',
        'padel_iq': 85.5,
        'metrics': {
            'positioning': 90,
            'technique': 85,
            'tactics': 80
        },
        'created_at': datetime.utcnow(),
        'task_id': 'test_task_123'
    }
"""
Configuración y fixtures para pruebas de Padelyzer.
"""
# Configuración de pruebas para pytest
import os
import sys
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# Agregar directorio raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar configuraciones y dependencias necesarias
from app.core.config import settings

# Mocks para Firebase
@pytest.fixture
def mock_firebase():
    """Fixture para mockear Firebase en pruebas."""
    mock = MagicMock()
    return mock

@pytest.fixture
def mock_firestore():
    """Fixture para mockear Firestore en pruebas."""
    mock = MagicMock()
    # Configurar el mock para simular operaciones de Firestore
    mock.collection.return_value.document.return_value.get.return_value.exists = True
    mock.collection.return_value.document.return_value.get.return_value.to_dict.return_value = {
        "test_field": "test_value"
    }
    return mock
import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Mock para Firestore
class MockFirestore:
    def __init__(self):
        self.data = {}

    def collection(self, name):
        if name not in self.data:
            self.data[name] = {}
        return MockCollection(self.data[name])

class MockCollection:
    def __init__(self, data):
        self.data = data

    def document(self, doc_id):
        if doc_id not in self.data:
            self.data[doc_id] = {}
        return MockDocument(self.data[doc_id])

class MockDocument:
    def __init__(self, data):
        self.data = data
        self._exists = True

    def get(self):
        doc_snapshot = Mock()
        doc_snapshot.exists = self._exists
        doc_snapshot.to_dict.return_value = self.data
        return doc_snapshot

    def set(self, data, merge=False):
        if merge:
            self.data.update(data)
        else:
            self.data = data
        return True

# Fixtures
@pytest.fixture
def mock_firestore():
    """Fixture que proporciona una instancia mock de Firestore"""
    with patch('app.config.firebase.firestore.client') as mock_client:
        firestore = MockFirestore()
        mock_client.return_value = firestore
        yield firestore

@pytest.fixture
def mock_storage():
    """Fixture que proporciona una instancia mock de Storage"""
    with patch('app.config.firebase.storage.bucket') as mock_bucket:
        yield mock_bucket

@pytest.fixture
def test_video():
    """Fixture que proporciona un archivo de video temporal para pruebas"""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
        temp_file.write(b"test video content")
        temp_file.flush()
        file_path = temp_file.name
        yield file_path
        # Limpiar después de la prueba
        if os.path.exists(file_path):
            os.unlink(file_path)
    # Crear un único mock_doc_snapshot que se usará en todas las llamadas
    class MockDocumentSnapshot:
        def __init__(self, data):
            self._data = data
            self.exists = True

        def to_dict(self):
            return self._data

    mock_doc_snapshot = MockDocumentSnapshot(test_data)

    # Configurar el mock para cualquier documento
    mock_document = MagicMock()
    mock_document.get.return_value = mock_doc_snapshot
    mock_document.set.return_value = None
    mock_document.update.return_value = None

    # Configurar la colección para devolver el documento mock
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_document

    # Configurar el mock_db para devolver la colección video_analyses
    def collection_side_effect(name, *args, **kwargs):
        if name == 'video_analyses':
            return mock_collection
        return MagicMock()
    mock_db.collection.side_effect = collection_side_effect

    with patch('firebase_admin.firestore.client', return_value=mock_db):
        yield mock_db

@pytest.fixture(autouse=True)
def patch_tasks_import():
    with patch.dict('sys.modules', {'tasks': MagicMock()}):
        yield

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
    from app.main import app
    return TestClient(app)

@pytest.fixture(scope="session")
def firestore_client():
    """Get a real Firestore client for integration tests."""
    return firestore.client()

@pytest.fixture
def mock_video():
    """Fixture para simular un video de prueba."""
    os.makedirs("tests/test_videos", exist_ok=True)
    video_path = "tests/test_videos/test_video.mp4"
    with open(video_path, "wb") as f:
        f.write(b"fake video content")
    yield {
        'url': video_path,
        'duration': 5,
        'resolution': (640, 480),
        'size': os.path.getsize(video_path)
    }
    if os.path.exists(video_path):
        os.remove(video_path)

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

@pytest.fixture
def firebase_app():
    """Fixture para simular la aplicación de Firebase."""
    return MagicMock()

@pytest.fixture
def mock_analysis_result():
    """Fixture para simular el resultado del análisis."""
    return {
        "padel_iq": 85.5,
        "metrics": {
            "tecnica": 90,
            "ritmo": 80,
            "fuerza": 85,
            "repeticion": 82
        },
        "force_category": "primera_fuerza",
        "player_level": "Avanzado"
    } 