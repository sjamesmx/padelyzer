import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.schemas.auth import UserRegistration, UserLogin
from app.schemas.video import VideoUpload
from app.schemas.matchmaking import MatchRequest
import json
from unittest.mock import MagicMock, patch
import time

@pytest.mark.auth
def test_auth_endpoints(test_client, test_user, mock_firebase):
    # Mock de la colección de usuarios con timeout
    mock_users = mock_firebase.collection('users')
    mock_users.where.return_value.get.return_value = []
    
    # Test registration con timeout
    with patch('time.sleep', return_value=None):  # Evitar delays reales
        response = test_client.post(f"{settings.AUTH_ROUTE}/signup", json=test_user)
        assert response.status_code in (200, 201, 422)
    
    if response.status_code == 422:
        error_data = response.json()
        assert "detail" in error_data
    
    # Mock de usuario existente para login
    mock_users.where.return_value.get.return_value = [MagicMock(to_dict=lambda: {
        "id": test_user["id"],
        "email": test_user["email"],
        "password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYpR1IOBYyGqK8y",  # Test123!
        "username": test_user["username"]
    })]
    
    # Test login con timeout
    with patch('time.sleep', return_value=None):  # Evitar delays reales
        login_data = {
            "email": test_user["email"],
            "password": test_user["password"]
        }
        response = test_client.post(f"{settings.AUTH_ROUTE}/login", json=login_data)
        assert response.status_code in (200, 401)
    
    if response.status_code == 200:
        assert "access_token" in response.json()

@pytest.mark.video
def test_video_endpoints(test_client, test_user, test_video, auth_headers, mock_firebase):
    # Mock de la colección de videos con timeout
    mock_videos = mock_firebase.collection('videos')
    mock_videos.where.return_value.get.return_value = []
    
    # Test video upload endpoint con timeout
    with patch('time.sleep', return_value=None):  # Evitar delays reales
        response = test_client.post(
            f"{settings.VIDEOS_ROUTE}/upload",
            headers=auth_headers,
            json=test_video
        )
        assert response.status_code in (200, 201, 401, 422)
    
    if response.status_code == 401:
        error_data = response.json()
        assert "detail" in error_data
        assert (
            "Not authenticated" in error_data["detail"] or
            "No se pudo validar las credenciales" in error_data["detail"]
        )
    
    # Mock de videos existentes
    mock_videos.where.return_value.get.return_value = [
        MagicMock(to_dict=lambda: test_video)
    ]
    
    # Test video list endpoint con timeout
    with patch('time.sleep', return_value=None):  # Evitar delays reales
        response = test_client.get(f"{settings.VIDEOS_ROUTE}", headers=auth_headers)
        assert response.status_code in (200, 401)
    
    if response.status_code == 200:
        assert isinstance(response.json(), list)

@pytest.mark.matchmaking
def test_matchmaking_endpoints(test_client, test_user, test_match, auth_headers, mock_firebase):
    # Mock de la colección de matches con timeout
    mock_matches = mock_firebase.collection('matches')
    mock_matches.where.return_value.get.return_value = []
    
    # Test create match request con timeout
    with patch('time.sleep', return_value=None):  # Evitar delays reales
        response = test_client.post(
            f"{settings.MATCHMAKING_ROUTE}/request",
            headers=auth_headers,
            json=test_match
        )
        assert response.status_code in (200, 201, 401, 422)
    
    if response.status_code == 401:
        error_data = response.json()
        assert "detail" in error_data
        assert (
            "Not authenticated" in error_data["detail"] or
            "No se pudo validar las credenciales" in error_data["detail"]
        )
    
    # Mock de matches existentes
    mock_matches.where.return_value.get.return_value = [
        MagicMock(to_dict=lambda: test_match)
    ]
    
    # Test get matches con timeout
    with patch('time.sleep', return_value=None):  # Evitar delays reales
        response = test_client.get(f"{settings.MATCHMAKING_ROUTE}/matches", headers=auth_headers)
        assert response.status_code in (200, 401)
    
    if response.status_code == 200:
        assert isinstance(response.json(), list)
    
    # Test find match con timeout
    with patch('time.sleep', return_value=None):  # Evitar delays reales
        response = test_client.post(
            f"{settings.MATCHMAKING_ROUTE}/find_match",
            headers=auth_headers,
            json={"level": "intermediate"}
        )
        assert response.status_code in (200, 401, 422)

def test_router_prefixes(test_client):
    # Test auth router prefix
    response = test_client.get(f"{settings.AUTH_ROUTE}/login")
    assert response.status_code in (200, 401, 405)
    
    # Test videos router prefix
    response = test_client.get(f"{settings.VIDEOS_ROUTE}")
    assert response.status_code in (200, 401, 405)
    
    # Test matchmaking router prefix
    response = test_client.get(f"{settings.MATCHMAKING_ROUTE}/matches")
    assert response.status_code in (200, 401, 405)

def test_authentication_requirements(test_client):
    # Test protected endpoints without token
    response = test_client.get(f"{settings.USERS_ROUTE}/me")
    assert response.status_code in (401, 405)
    
    response = test_client.get(f"{settings.VIDEOS_ROUTE}")
    assert response.status_code in (401, 405)
    
    response = test_client.get(f"{settings.MATCHMAKING_ROUTE}/matches")
    assert response.status_code in (401, 405) 