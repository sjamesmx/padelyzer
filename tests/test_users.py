import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_user_me_not_implemented():
    response = client.get("/api/v1/users/me")
    assert response.status_code == 501
    assert "Función no implementada" in response.text

def test_update_user_me_not_implemented():
    user_update = {
        "name": "Nuevo Nombre",
        "nivel": "avanzado",
        "posicion_preferida": "izquierda"
    }
    response = client.put("/api/v1/users/me", json=user_update)
    assert response.status_code == 501
    assert "Función no implementada" in response.text

def test_read_user_profile_not_implemented():
    response = client.get("/api/v1/users/testuser/profile", params={"level": "intermediate"})
    assert response.status_code == 501
    assert "Not Implemented" in response.text

def test_update_user_profile_not_implemented():
    response = client.put("/api/v1/users/testuser/profile", json={"nivel": "intermedio"})
    assert response.status_code == 501
    assert "Not Implemented" in response.text 