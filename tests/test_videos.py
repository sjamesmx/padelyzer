import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from datetime import timedelta, datetime
from app.core.config import settings
from app.schemas.user import UserPreferences, UserStats

TEST_USER_EMAIL = "test@example.com"
TEST_USER_ID = "test_user_id"

def get_test_token():
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": TEST_USER_EMAIL},
        expires_delta=access_token_expires
    )

@pytest.fixture(scope="function", autouse=True)
def create_test_user(firestore_client):
    """Create a test user before each test and clean up after."""
    users_ref = firestore_client.collection('users')
    
    # Clean up any existing test user
    query = users_ref.where('email', '==', TEST_USER_EMAIL).get()
    for doc in query:
        doc.reference.delete()
    
    # Create test user with all required fields
    user_data = {
        "id": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "name": "Test User",
        "nivel": "intermedio",
        "posicion_preferida": "derecha",
        "email_verified": True,
        "is_active": True,
        "fecha_registro": datetime.utcnow(),
        "preferences": UserPreferences().model_dump(),
        "stats": UserStats().model_dump(),
        "achievements": [],
        "blocked_users": [],
        "padel_iq": 100.0,
        "clubs": [],
        "availability": [],
        "location": None,
        "onboarding_status": "pending",
        "last_login": None
    }
    
    # Create the user
    users_ref.document(TEST_USER_ID).set(user_data)
    
    # Verify user creation
    created = users_ref.where('email', '==', TEST_USER_EMAIL).get()
    assert len(created) > 0, "Test user was not created in Firestore!"
    
    yield
    
    # Clean up after test
    users_ref.document(TEST_USER_ID).delete()

@pytest.fixture
def auth_headers():
    token = get_test_token()
    return {"Authorization": f"Bearer {token}"}

def test_upload_training_video(test_client, auth_headers, create_test_user):
    response = test_client.post(
        "/api/v1/videos/training",
        headers=auth_headers,
        json={
            "video_url": "https://example.com/video.mp4",
            "description": "Test video"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "video_id" in data
    assert isinstance(data["video_id"], str)

def test_analyze_video(test_client, auth_headers, create_test_user):
    # First upload a video
    upload_response = test_client.post(
        "/api/v1/videos/training",
        headers=auth_headers,
        json={
            "video_url": "https://example.com/video.mp4",
            "description": "Test video"
        }
    )
    assert upload_response.status_code == 200
    video_id = upload_response.json()["video_id"]

    # Then analyze it
    response = test_client.post(
        "/api/v1/videos/analyze",
        headers=auth_headers,
        json={"video_id": video_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert isinstance(data["analysis_id"], str)

def test_upload_video_unauthorized(test_client):
    response = test_client.post(
        "/api/v1/videos/training",
        json={
            "video_url": "https://example.com/video.mp4",
            "description": "Test video"
        }
    )
    assert response.status_code == 401

def test_analyze_video_unauthorized(test_client):
    response = test_client.post(
        "/api/v1/videos/analyze",
        json={"video_id": "test_id"}
    )
    assert response.status_code == 401 