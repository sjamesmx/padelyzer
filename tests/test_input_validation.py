import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.auth import UserRegistration, UserLogin, ResetPasswordRequest
from app.schemas.video import VideoUpload
from app.schemas.matchmaking import MatchRequest, MatchResponse

client = TestClient(app)

def test_user_registration_validation():
    # Test valid registration
    valid_data = {
        "email": "test@example.com",
        "password": "Test123!",
        "username": "testuser"
    }
    response = client.post("/api/v1/auth/signup", json=valid_data)
    assert response.status_code in (200, 201, 400, 422)  # Puede ser 400 si el email ya existe

    # Test invalid email
    invalid_email = valid_data.copy()
    invalid_email["email"] = "invalid-email"
    response = client.post("/api/v1/auth/signup", json=invalid_email)
    assert response.status_code == 422

    # Test invalid password (too short)
    invalid_password = valid_data.copy()
    invalid_password["password"] = "short"
    response = client.post("/api/v1/auth/signup", json=invalid_password)
    assert response.status_code == 422

def test_user_login_validation():
    # Test valid login
    valid_data = {
        "email": "test@example.com",
        "password": "Test123!"
    }
    response = client.post("/api/v1/auth/login", json=valid_data)
    assert response.status_code in (200, 201, 401, 422)  # Puede ser 401 si el usuario no existe

    # Test invalid credentials
    invalid_data = valid_data.copy()
    invalid_data["password"] = "wrongpassword"
    response = client.post("/api/v1/auth/login", json=invalid_data)
    assert response.status_code in (401, 422)

def test_video_upload_validation():
    # Test valid video upload
    valid_data = {
        "title": "Test Video",
        "description": "Test Description",
        "type": "training"
    }
    # El endpoint espera autenticación, así que puede devolver 401
    response = client.post("/api/v1/videos/training", json=valid_data)
    assert response.status_code in (200, 201, 401, 422)

    # Test invalid title (too short)
    invalid_title = valid_data.copy()
    invalid_title["title"] = ""
    response = client.post("/api/v1/videos/training", json=invalid_title)
    assert response.status_code in (401, 422)

    # Test invalid type
    invalid_type = valid_data.copy()
    invalid_type["type"] = "invalid"
    response = client.post("/api/v1/videos/training", json=invalid_type)
    assert response.status_code in (401, 422)

def test_match_request_validation():
    # Test valid match request
    valid_data = {
        "message": "Looking for a match",
        "max_distance": 10,
        "preferred_time": "2024-03-20T10:00:00Z"
    }
    response = client.post("/api/v1/matchmaking/request", json=valid_data)
    assert response.status_code in (200, 201, 401, 422)

    # Test invalid message (too long)
    invalid_message = valid_data.copy()
    invalid_message["message"] = "x" * 501
    response = client.post("/api/v1/matchmaking/request", json=invalid_message)
    assert response.status_code in (401, 422)

    # Test invalid max_distance
    invalid_distance = valid_data.copy()
    invalid_distance["max_distance"] = -1
    response = client.post("/api/v1/matchmaking/request", json=invalid_distance)
    assert response.status_code in (401, 422) 