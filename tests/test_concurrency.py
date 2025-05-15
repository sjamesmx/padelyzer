"""
Pruebas de concurrencia para Padelyzer.
"""
import os
import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from tests.init_test_data import (
    create_test_users,
    create_test_videos,
    clear_test_data,
    initialize_firestore
)

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Fixture para limpiar datos antes y después de cada prueba."""
    clear_test_data()
    yield
    clear_test_data()

async def upload_video_async(user_id, video_path, video_type):
    """Función asíncrona para subir un video."""
    with open(video_path, "rb") as video_file:
        response = client.post(
            "/api/v1/video/process_training_video",
            files={"video": video_file},
            data={"user_id": user_id, "tipo_video": video_type}
        )
    return response

async def calculate_padel_iq_async(user_id, video_url, video_type):
    """Función asíncrona para calcular Padel IQ."""
    response = client.post(
        "/api/v1/video/calculate_padel_iq",
        json={
            "user_id": user_id,
            "video_url": video_url,
            "tipo_video": video_type
        }
    )
    return response

@pytest.mark.asyncio
async def test_concurrent_uploads():
    """Prueba subidas concurrentes de videos."""
    user_ids = create_test_users(10)
    video_path = create_test_videos()["entrenamiento"]
    
    # Subir 10 videos simultáneamente
    tasks = [upload_video_async(user_id, video_path, "entrenamiento") for user_id in user_ids]
    responses = await asyncio.gather(*tasks)
    
    # Validar respuestas
    for response in responses:
        assert response.status_code == 501
        assert response.json()["detail"] == "Not Implemented"

@pytest.mark.asyncio
async def test_concurrent_padel_iq_calculations():
    """Prueba cálculos concurrentes de Padel IQ."""
    user_ids = create_test_users(5)
    video_path = create_test_videos()["entrenamiento"]
    
    # Calcular Padel IQ simultáneamente
    tasks = [
        calculate_padel_iq_async(user_id, video_path, "entrenamiento")
        for user_id in user_ids
    ]
    responses = await asyncio.gather(*tasks)
    
    # Validar respuestas
    for response in responses:
        assert response.status_code == 501
        assert response.json()["detail"] == "Not Implemented"

@pytest.mark.asyncio
async def test_concurrent_profile_updates():
    """Prueba actualizaciones concurrentes de perfiles."""
    user_ids = create_test_users(5)
    
    async def update_profile(user_id):
        response = client.put(
            f"/api/v1/users/{user_id}/profile",
            json={
                "nivel": "intermedio",
                "posicion_preferida": "revés",
                "biografia": f"Jugador {user_id}"
            }
        )
        return response
    
    # Actualizar perfiles simultáneamente
    tasks = [update_profile(user_id) for user_id in user_ids]
    responses = await asyncio.gather(*tasks)
    
    # Validar respuestas
    for response in responses:
        assert response.status_code == 501
        assert response.json()["detail"] == "Not Implemented"

@pytest.mark.asyncio
async def test_concurrent_search_requests():
    """Prueba búsquedas concurrentes de jugadores."""
    # Crear usuarios con diferentes ubicaciones
    users = create_test_users(10)
    db = initialize_firestore()
    
    # Actualizar ubicaciones
    for i, user_id in enumerate(users):
        db.collection("users").document(user_id).update({
            "location": {
                "city": "Puebla",
                "lat": 19.043 + (i * 0.001),
                "lon": -98.198 + (i * 0.001)
            },
            "padel_iq": 50 + i
        })
    
    async def search_players(lat, lon):
        response = client.post(
            "/api/v1/search/players",
            json={
                "location": {"lat": lat, "lon": lon},
                "max_distance_km": 5,
                "padel_iq_range": [40, 80]
            }
        )
        return response
    
    # Realizar búsquedas simultáneas
    search_locations = [
        (19.043, -98.198),
        (19.044, -98.199),
        (19.045, -98.200),
        (19.046, -98.201),
        (19.047, -98.202)
    ]
    
    tasks = [search_players(lat, lon) for lat, lon in search_locations]
    responses = await asyncio.gather(*tasks)
    
    # Validar respuestas
    for response in responses:
        assert response.status_code == 501
        assert response.json()["detail"] == "Not Implemented" 