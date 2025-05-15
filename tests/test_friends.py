import pytest
from fastapi.testclient import TestClient
from app.main import app
from datetime import datetime
from unittest.mock import patch
import sys
import types
import asyncio

client = TestClient(app)

# Mock de usuario autenticado
class MockUser:
    id = "current_user_id"
    name = "Usuario Test"
    email = "test@example.com"
    username = "testuser"

async def async_mock_get_current_user():
    return MockUser()

@pytest.fixture(autouse=True)
def patch_get_current_user(monkeypatch):
    # Patch en el módulo de endpoints donde se importa la dependencia
    monkeypatch.setattr(
        "app.api.v1.endpoints.friends.get_current_user",
        async_mock_get_current_user
    )

# ---------- TESTS PARA BLOQUEO DE USUARIOS ----------
def test_block_user_success(mocker):
    mock_db = mocker.Mock()
    mock_blocks = mocker.Mock()
    mock_friendships = mocker.Mock()
    mock_requests = mocker.Mock()
    mock_query = mocker.Mock()
    
    # Mock para verificar bloqueo existente
    mock_blocks.where.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.get.return_value = []
    
    # Mock para eliminar amistades
    mock_friendships.where.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.get.return_value = []
    
    # Mock para eliminar solicitudes
    mock_requests.where.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.get.return_value = []
    
    mock_db.collection.side_effect = lambda x: {
        'blocked_users': mock_blocks,
        'friendships': mock_friendships,
        'friendship_requests': mock_requests
    }[x]
    
    mocker.patch("app.services.firebase.get_firebase_client", return_value=mock_db)
    
    # Bloquear usuario
    response = client.post(
        "/api/v1/friends/block/user123",
        json={"reason": "Comportamiento inapropiado"},
        headers={"Authorization": "Bearer testtoken"}
    )
    assert response.status_code == 200
    assert response.json()["blocker_id"] == "current_user_id"
    assert response.json()["blocked_id"] == "user123"
    assert response.json()["reason"] == "Comportamiento inapropiado"

def test_block_user_already_blocked(mocker):
    mock_db = mocker.Mock()
    mock_blocks = mocker.Mock()
    mock_query = mocker.Mock()
    
    # Mock para simular usuario ya bloqueado
    mock_blocks.where.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_query.get.return_value = [mocker.Mock()]
    
    mock_db.collection.return_value = mock_blocks
    mocker.patch("app.services.firebase.get_firebase_client", return_value=mock_db)
    
    # Intentar bloquear usuario ya bloqueado
    response = client.post(
        "/api/v1/friends/block/user123",
        json={"reason": "Comportamiento inapropiado"},
        headers={"Authorization": "Bearer testtoken"}
    )
    assert response.status_code == 400
    assert "Usuario ya bloqueado" in response.json()["detail"]

def test_list_blocked_users(mocker):
    mock_db = mocker.Mock()
    mock_blocks = mocker.Mock()
    mock_query = mocker.Mock()
    mock_doc = mocker.Mock()
    
    # Mock para simular usuarios bloqueados
    mock_doc.id = "block123"
    mock_doc.to_dict.return_value = {
        "blocker_id": "current_user_id",
        "blocked_id": "user123",
        "reason": "Comportamiento inapropiado",
        "created_at": datetime.now()
    }
    mock_query.get.return_value = [mock_doc]
    mock_blocks.where.return_value = mock_query
    mock_db.collection.return_value = mock_blocks
    
    mocker.patch("app.services.firebase.get_firebase_client", return_value=mock_db)
    
    # Listar usuarios bloqueados
    response = client.get(
        "/api/v1/friends/blocked",
        headers={"Authorization": "Bearer testtoken"}
    )
    assert response.status_code == 200
    assert len(response.json()["blocked_users"]) == 1
    assert response.json()["blocked_users"][0]["blocked_id"] == "user123"

def test_unblock_user_success(mocker):
    mock_db = mocker.Mock()
    mock_blocks = mocker.Mock()
    mock_query = mocker.Mock()
    mock_doc = mocker.Mock()
    
    # Mock para simular usuario bloqueado
    mock_doc.reference = mocker.Mock()
    mock_query.get.return_value = [mock_doc]
    mock_blocks.where.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_db.collection.return_value = mock_blocks
    
    mocker.patch("app.services.firebase.get_firebase_client", return_value=mock_db)
    
    # Desbloquear usuario
    response = client.delete(
        "/api/v1/friends/block/user123",
        headers={"Authorization": "Bearer testtoken"}
    )
    assert response.status_code == 200
    assert "Usuario desbloqueado correctamente" in response.json()["detail"]

def test_unblock_user_not_blocked(mocker):
    mock_db = mocker.Mock()
    mock_blocks = mocker.Mock()
    mock_query = mocker.Mock()
    
    # Mock para simular usuario no bloqueado
    mock_query.get.return_value = []
    mock_blocks.where.return_value = mock_query
    mock_query.where.return_value = mock_query
    mock_db.collection.return_value = mock_blocks
    
    mocker.patch("app.services.firebase.get_firebase_client", return_value=mock_db)
    
    # Intentar desbloquear usuario no bloqueado
    response = client.delete(
        "/api/v1/friends/block/user123",
        headers={"Authorization": "Bearer testtoken"}
    )
    assert response.status_code == 404
    assert "Usuario no bloqueado" in response.json()["detail"] 