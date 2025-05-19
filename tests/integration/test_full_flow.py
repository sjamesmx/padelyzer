import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock
import uuid
import json
import os
import tempfile

client = TestClient(app)

def test_full_user_flow():
    # Generate unique email
    unique_email = f"test_{uuid.uuid4()}@example.com"
    
    # 1. Register user
    register_data = {
        "email": unique_email,
        "password": "Test123!",
        "name": "Test User",
        "nivel": "principiante",
        "posicion_preferida": "derecha"
    }
    
    register_response = client.post("/api/v1/auth/register", json=register_data)
    assert register_response.status_code == 200
    user_data = register_response.json()
    assert user_data["email"] == unique_email
    
    # 2. Verify email (development mode)
    verify_response = client.post(
        "/api/v1/auth/verify-email",
        json={"token": user_data["id"]}
    )
    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert "detail" in verify_data
    assert "verificado correctamente" in verify_data["detail"]
    
    # 3. Login
    login_data = {
        "email": unique_email,
        "password": "Test123!"
    }
    login_response = client.post("/api/v1/auth/login", json=login_data)
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    token = login_data["access_token"]
    
    # 4. Upload video
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
        temp_file.write(b"fake video content")
        temp_file.flush()
        
        with open(temp_file.name, "rb") as video_file:
            upload_response = client.post(
                "/api/v1/video/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("test.mp4", video_file, "video/mp4")},
                data={
                    "video_type": "training",
                    "description": "Test video",
                    "player_position": "derecha"
                }
            )
    
    os.unlink(temp_file.name)
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert "video_id" in upload_data
    assert "url" in upload_data
    assert upload_data["status"] in ("pending", "processing", "completed", "failed")
    
    # 5. Get Padel IQ
    with patch('app.services.firebase.get_firebase_client') as mock_firebase:
        mock_db = MagicMock()
        mock_firebase.return_value = (mock_db, MagicMock())
        
        # Mock the Padel IQ data
        mock_db.collection().document().get().to_dict.return_value = {
            "padel_iq": 85,
            "last_updated": "2024-03-20T12:00:00Z"
        }
        
        iq_response = client.get(
            f"/api/v1/users/{user_data['id']}/padel-iq",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert iq_response.status_code == 200
        iq_data = iq_response.json()
        assert "padel_iq" in iq_data
        assert isinstance(iq_data["padel_iq"], (int, float)) 